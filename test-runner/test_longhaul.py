# Copyrigh (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest
import json
import threading
import six
import abc
import datetime

from longhaul_config import Telemetry, DesiredTestProperties, ReportedTestProperties
from measurement import MeasureSimpleCount, MeasureRunningCodeBlock, MeasureLatency
from horton_logging import logger

pytestmark = pytest.mark.asyncio


desired_node_config = {
    "test_config": {
        "d2c": {
            "enabled": True,
            "interval": 1,
            "ops_per_interval": 10,
            "slow_init_threshold": "0:00:02",
            "slow_complete_threshold": "0:00:05",
        },
        "scenario": "test_longhaul_d2c_simple",
        "total_duration": "1:00:00",
    }
}


@six.add_metaclass(abc.ABCMeta)
class LongHaulOp(object):
    def __init__(self, config, stats, progress):
        self.config = config
        self.stats = stats
        self.progress = progress

        self.count_in_progress = MeasureRunningCodeBlock("in_progress", logger=None)
        self.count_initiating = MeasureRunningCodeBlock("initiating", logger=None)
        self.count_completing = MeasureRunningCodeBlock("completing", logger=None)

        self.count_completed = MeasureSimpleCount()
        self.count_failed = MeasureSimpleCount()
        self.count_slow_initiate = MeasureSimpleCount()
        self.count_slow_complete = MeasureSimpleCount()

    @abc.abstractmethod
    async def run_one_op(self):
        pass

    async def schedule_one_interval(self):
        return set(
            [
                asyncio.create_task(self.run_one_op())
                for _ in range(0, self.config.ops_per_interval)
            ]
        )

    async def update_stats(self):
        # BKTODO: get this all in one place
        self.stats.ops_completed = self.count_completed.get_count()
        self.stats.ops_in_progress = self.count_in_progress.get_count()
        self.stats.ops_failed = self.count_failed.get_count()
        self.stats.ops_slow_initiate = self.count_slow_initiate.get_count()
        self.stats.ops_slow_complete = self.count_slow_complete.get_count()

        self.progress.ops_completed = self.count_completed.get_count()
        self.progress.ops_in_progress = self.count_in_progress.get_count()
        self.progress.ops_failed = self.count_failed.get_count()
        self.progress.ops_slow_initiate = self.count_slow_initiate.get_count()
        self.progress.ops_slow_complete = self.count_slow_complete.get_count()


class LongHaulOpD2c(LongHaulOp):
    def __init__(self, config, stats, progress, client, eventhub):
        super(LongHaulOpD2c, self).__init__(config, stats, progress)

        self.client = client
        self.eventhub = eventhub

        self.next_message_id = MeasureSimpleCount()

        self.mid_list = {}
        self.mid_list_lock = threading.Lock()
        self.listener = None

    async def run_one_op(self):
        measure_initiate = MeasureLatency()
        measure_complete = MeasureLatency()

        with self.count_in_progress, measure_complete:
            mid = self.next_message_id.increment()

            with self.count_initiating, measure_initiate:
                await self.update_stats()

                telemetry = Telemetry()
                telemetry.horton_mid = mid
                telemetry.progress = self.progress

                # BKTODO when this scales, this needs to happen somewhere else.
                telemetry.progress.update(
                    ops_completed=self.count_completed.get_count(),
                    ops_in_progress=self.count_in_progress.get_count(),
                    ops_waiting_to_initiate=self.count_initiating.get_count(),
                    ops_waiting_to_complete=self.count_completing.get_count(),
                    ops_slow_initiate=self.count_slow_initiate.get_count(),
                    ops_slow_complete=self.count_slow_complete.get_count(),
                )

                await self.client.send_event(telemetry.to_dict(mid))

            with self.count_completing:
                await self.update_stats()
                await self.wait_for_completion(mid)

        if measure_complete.get_latency() > self.config.slow_complete_threshold:
            self.count_slow_initiate.increment()
        if measure_initiate.get_latency() > self.config.slow_init_threshold:
            self.count_slow_complete.increment()
        self.count_completed.increment()

        await self.update_stats()

    async def listen_on_eventhub(self):
        while True:
            message = await self.eventhub.wait_for_next_event(self.client.device_id)

            try:
                message = json.loads(message)
            except (AttributeError, TypeError):
                pass

            if isinstance(message, dict) and "horton_mid" in message:
                mid = message["horton_mid"]
                with self.mid_list_lock:
                    if mid in self.mid_list:
                        if isinstance(self.mid_list[mid], asyncio.Future):
                            self.mid_list[mid].set_result(True)
                        del self.mid_list[mid]
                    else:
                        self.mid_list[mid] = True

    async def wait_for_completion(self, mid):
        message_received = asyncio.Future()

        with self.mid_list_lock:
            # if we've received it, return.  Else, set a future for the listener to complete when it does receive.
            if mid in self.mid_list:
                del self.mid_list[mid]
                return
            else:
                self.mid_list[mid] = message_received

            # see if the previous listener is done.
            if self.listener and self.listener.done():
                # call result() to force an exception if the listener had one
                self.listener.result()
                self.listener = None

            # start a new future
            if self.listener is None:
                self.listener = asyncio.create_task(self.listen_on_eventhub())

        await message_received

    async def finish(self):
        if self.listener:
            self.listener.cancel()
            self.listener = None


class LongHaulTest(object):
    async def test_longhaul(self, client, eventhub):
        await eventhub.connect()

        test_config = DesiredTestProperties.from_dict(desired_node_config).test_config

        test_report = ReportedTestProperties()
        test_report.test_config = test_config
        test_report.progress.total_duration = test_config.total_duration
        test_report.progress.status = "running"

        async def report_loop():
            while True:
                patch = {"reported": test_report.to_dict()}
                logger("reporting: {}".format(patch))
                await client.patch_twin(patch)

                await asyncio.sleep(5)  # todo: make configurable.

        # BKTODO: maybe just pass in test_config and test_report and let the runner decide what to use?
        runner = LongHaulOpD2c(
            test_config.d2c,
            test_report.test_stats.d2c,
            test_report.progress,
            client,
            eventhub,
        )

        try:
            all_tasks = set([asyncio.create_task(report_loop())])

            while (
                test_report.progress.elapsed_time < test_report.progress.total_duration
                or test_report.progress.elapsed_time == datetime.timedelta(0)
            ):

                all_tasks.update(await runner.schedule_one_interval())

                logger("before sleep: {} tasks in list".format(len(all_tasks)))

                # BKtODO: other intervals besides 1, interleave ops with different intervals
                done, pending = await asyncio.wait(
                    all_tasks, timeout=1, return_when=asyncio.FIRST_EXCEPTION
                )
                await asyncio.gather(*done)

                logger(
                    "after sleep: {} done, {} pending".format(len(done), len(pending))
                )

                all_tasks = pending

            await runner.finish()

            test_report.progress.status = "completed"

        except Exception:
            test_report.progress.status = "failed"
            raise

        finally:
            # BKTODO: maybe signal the reporter to finish?
            patch = {"reported": test_report.to_dict()}
            logger("reporting: {}".format(patch))
            await client.patch_twin(patch)


@pytest.mark.testgroup_iothub_device_2h_stress
@pytest.mark.describe("Device Client Long Run")
class TestDeviceClientLongHaul(LongHaulTest):
    @pytest.fixture
    def client(self, test_device):
        return test_device


@pytest.mark.testgroup_iothub_module_2h_stress
@pytest.mark.describe("Device Client Long Run")
class TestModuleClientLongHaul(LongHaulTest):
    @pytest.fixture
    def client(self, test_module):
        return test_module
