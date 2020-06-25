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
from measurement import (
    MeasureSimpleCount,
    MeasureRunningCodeBlock,
    MeasureLatency,
    GatherStatistics,
)
from horton_logging import logger

pytestmark = pytest.mark.asyncio


desired_node_config = {
    "test_config": {
        "d2c": {
            "enabled": True,
            "interval": 1,
            "ops_per_interval": 10,
            "slow_send_threshold": "0:00:02",
            "slow_send_and_receive_threshold": "0:00:05",
        },
        "scenario": "test_longhaul_d2c_simple",
        "total_duration": "0:05:00",
    }
}


@six.add_metaclass(abc.ABCMeta)
class LongHaulOp(object):
    def __init__(self, config, stats, progress):
        self.config = config
        self.stats = stats
        self.progress = progress

        self.count_sending = MeasureRunningCodeBlock("sending", logger=None)
        self.count_completing = MeasureRunningCodeBlock("completing", logger=None)

        self.count_completed = MeasureSimpleCount()
        self.count_failed = MeasureSimpleCount()

        self.gather_send_stats = GatherStatistics(
            "send latency",
            slowness_threshold=config.slow_send_threshold.total_seconds(),
        )
        self.gather_send_and_receive_stats = GatherStatistics(
            "send and receive latency",
            slowness_threshold=config.slow_send_and_receive_threshold.total_seconds(),
        )

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
        send_stats = self.gather_send_stats.get_stats()
        send_and_receive_stats = self.gather_send_and_receive_stats.get_stats()

        self.stats.ops_completed = self.count_completed.get_count()
        self.stats.ops_failed = self.count_failed.get_count()
        self.stats.ops_waiting_to_send = self.count_sending.get_count()
        self.stats.ops_waiting_to_complete = self.count_completing.get_count()
        self.stats.ops_slow_send = send_stats.slow
        self.stats.ops_slow_send_and_receive = send_and_receive_stats.slow
        self.stats.mean_send_latency = send_stats.mean
        self.stats.fiftieth_percentile_send_latency = send_stats.fiftieth_percentile
        self.stats.mean_send_and_receive_latency = send_and_receive_stats.mean
        self.stats.fiftieth_percentile_send_and_receive_latency = (
            send_and_receive_stats.fiftieth_percentile
        )

        self.progress.ops_completed = self.count_completed.get_count()
        self.progress.ops_failed = self.count_failed.get_count()
        self.progress.ops_waiting_to_send = self.count_sending.get_count()
        self.progress.ops_waiting_to_complete = self.count_completing.get_count()
        self.progress.ops_slow_send = send_stats.slow
        self.progress.ops_slow_send_and_receive = send_and_receive_stats.slow
        self.progress.mean_send_latency = send_stats.mean
        self.progress.fiftieth_percentile_send_latency = send_stats.fiftieth_percentile
        self.progress.mean_send_and_receive_latency = send_and_receive_stats.mean
        self.progress.fiftieth_percentile_send_and_receive_latency = (
            send_and_receive_stats.fiftieth_percentile
        )


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

        measure_send_latency = MeasureLatency()
        measure_send_and_receive_latency = MeasureLatency()

        with measure_send_and_receive_latency:
            horton_mid = self.next_message_id.increment()

            with self.count_sending, measure_send_latency:
                await self.update_stats()

                telemetry = Telemetry()
                telemetry.progress = self.progress

                # BKTODO when this scales, this needs to happen somewhere else.
                await self.update_stats()
                telemetry.progress.update()
                await self.client.send_event(telemetry.to_dict(horton_mid))
            self.gather_send_stats.add_sample(measure_send_latency.get_latency())

            with self.count_completing:
                await self.update_stats()
                await self.wait_for_completion(horton_mid)

        self.gather_send_and_receive_stats.add_sample(
            measure_send_and_receive_latency.get_latency()
        )

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

        stop_reporter = False

        async def report_loop():
            stop_after_sending = False
            while True:
                if stop_reporter:
                    stop_after_sending = True

                patch = {"reported": test_report.to_dict()}
                logger("reporting: {}".format(patch))
                await client.patch_twin(patch)

                if stop_after_sending:
                    return

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
            reporter = asyncio.create_task(report_loop())
            all_tasks = set()

            while (
                test_report.progress.elapsed_time < test_report.progress.total_duration
                or test_report.progress.elapsed_time == datetime.timedelta(0)
            ):

                all_tasks.update(await runner.schedule_one_interval())

                logger("before sleep: {} tasks in list".format(len(all_tasks)))

                # BKtODO: other intervals besides 1, interleave ops with different intervals
                wait_time = MeasureLatency()
                interval_time = 1
                with wait_time:
                    done, pending = await asyncio.wait(
                        all_tasks,
                        timeout=interval_time,
                        return_when=asyncio.FIRST_EXCEPTION,
                    )
                    await asyncio.gather(*done)
                if wait_time.get_latency() < interval_time:
                    await asyncio.sleep(interval_time - wait_time.get_latency())

                if reporter.done():
                    # use await to pull the exception out of the Task.  If it doesn't
                    # raise, then raise our own exxception.
                    await reporter.result()
                    raise Exception("reporter task completed prematurely")

                logger(
                    "after sleep: {} done, {} pending".format(len(done), len(pending))
                )

                all_tasks = pending

            logger("XX wsiting for runner to finish")
            await runner.finish()

            logger("XX gathering all tasks")
            await asyncio.gather(*all_tasks)

            logger("XX marking as complete")
            test_report.progress.status = "completed"

        except Exception:
            test_report.progress.status = "failed"
            raise

        finally:
            logger("XX Stopping the reporter")
            stop_reporter = True
            await reporter


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
