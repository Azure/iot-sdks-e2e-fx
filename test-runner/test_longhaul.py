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
import gc

from longhaul_config import Telemetry, DesiredTestProperties, ReportedTestProperties
from measurement import (
    MeasureSimpleCount,
    MeasureRunningCodeBlock,
    MeasureLatency,
    GatherStatistics,
)
from horton_logging import logger

pytestmark = pytest.mark.asyncio

# BKTODO:
# add control to stop test


desired_node_config = {
    "test_config": {
        "d2c": {
            "enabled": True,
            "interval": 1,
            "ops_per_interval": 10,
            "slow_send_threshold": "0:00:02",
            "slow_send_and_receive_threshold": "0:00:05",
        },
        "total_duration": "0:00:30",
    }
}


@six.add_metaclass(abc.ABCMeta)
class LongHaulOp(object):
    def __init__(self, *, test_config, op_config, op_status):
        self.op_config = op_config
        self.op_status = op_status
        self.test_config = test_config

        self.count_sending = MeasureRunningCodeBlock("sending", logger=None)
        self.count_completing = MeasureRunningCodeBlock("completing", logger=None)

        self.count_completed = MeasureSimpleCount()
        self.count_failed = MeasureSimpleCount()

        self.gather_send_stats = GatherStatistics(
            "send latency",
            slowness_threshold=op_config.slow_send_threshold.total_seconds(),
            window_count=test_config.stats_window_op_count,
        )
        self.gather_send_and_receive_stats = GatherStatistics(
            "send and receive latency",
            slowness_threshold=op_config.slow_send_and_receive_threshold.total_seconds(),
            window_count=test_config.stats_window_op_count,
        )

    @abc.abstractmethod
    async def do_send(self, op_id):
        pass

    @abc.abstractmethod
    async def do_receive(self, op_id):
        pass

    async def run_one_op(self):
        measure_send_latency = MeasureLatency()
        measure_send_and_receive_latency = MeasureLatency()

        with measure_send_and_receive_latency:
            op_id = self.next_message_id.increment()

            with self.count_sending, measure_send_latency:
                await self.do_send(op_id)

            self.gather_send_stats.add_sample(measure_send_latency.get_latency())

            with self.count_completing:
                await self.do_receive(op_id)

        self.gather_send_and_receive_stats.add_sample(
            measure_send_and_receive_latency.get_latency()
        )

        self.count_completed.increment()
        await self.update_op_status()

    async def schedule_one_interval(self):
        return set(
            [
                asyncio.wait_for(
                    self.run_one_op(),
                    timeout=self.test_config.timeout_interval.total_seconds(),
                )
                for _ in range(0, self.op_config.ops_per_interval)
            ]
        )

    async def update_op_status(self):
        send_stats = self.gather_send_stats.get_stats()
        send_and_receive_stats = self.gather_send_and_receive_stats.get_stats()

        self.op_status.ops_completed = self.count_completed.get_count()
        self.op_status.ops_failed = self.count_failed.get_count()
        self.op_status.ops_waiting_to_send = self.count_sending.get_count()
        self.op_status.ops_waiting_to_complete = self.count_completing.get_count()
        self.op_status.ops_slow_send = send_stats.slow
        self.op_status.ops_slow_send_and_receive = send_and_receive_stats.slow
        self.op_status.mean_send_latency = send_stats.mean
        self.op_status.mean_send_and_receive_latency = send_and_receive_stats.mean


class LongHaulOpD2c(LongHaulOp):
    def __init__(self, test_config, test_status, client, eventhub):
        super(LongHaulOpD2c, self).__init__(
            test_config=test_config,
            op_config=test_config.d2c,
            op_status=test_status.d2c,
        )

        self.client = client
        self.eventhub = eventhub
        self.test_status = test_status

        self.next_message_id = MeasureSimpleCount()

        self.mid_list = {}
        self.mid_list_lock = threading.Lock()
        self.listener = None

    async def do_send(self, op_id):
        telemetry = Telemetry()
        telemetry.test_status = self.test_status

        await self.client.send_event(telemetry.to_dict(op_id))

    async def do_receive(self, op_id):
        await self.wait_for_completion(op_id)

    async def listen_on_eventhub(self):
        while True:
            message = await self.eventhub.wait_for_next_event(self.client.device_id)

            try:
                message = json.loads(message)
            except (AttributeError, TypeError):
                pass

            if isinstance(message, dict) and "op_id" in message:
                mid = message["op_id"]
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
        test_status = test_report.test_status
        test_status.status = "running"

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
        runner = LongHaulOpD2c(test_config, test_status, client, eventhub)

        try:
            reporter = asyncio.create_task(report_loop())
            all_tasks = set()

            while (
                test_status.elapsed_time < test_config.total_duration
                or test_status.elapsed_time == datetime.timedelta(0)
            ):

                await self.update_test_status(test_status)

                all_tasks.update(await runner.schedule_one_interval())

                interval_time = 1

                wait_time = MeasureLatency()
                with wait_time:
                    while len(all_tasks) and wait_time.get_latency() < interval_time:
                        done, pending = await asyncio.wait(
                            all_tasks,
                            timeout=interval_time,
                            return_when=asyncio.FIRST_EXCEPTION,
                        )

                        try:
                            await asyncio.gather(*done)
                        except Exception:
                            # BKTODO: this is where we would report an error to the event stream
                            test_status.ops_failed += 1
                            if (
                                test_status.ops_failed
                                > test_config.max_allowed_failures
                            ):
                                raise Exception(
                                    "failure count exceeded maximum allowed"
                                )

                        all_tasks = pending

                    if len(all_tasks) == 0:
                        await asyncio.sleep(interval_time - wait_time.get_latency())

                if reporter.done():
                    # use await to pull the exception out of the Task.  If it doesn't
                    # raise, then raise our own exxception.
                    await reporter.result()
                    raise Exception("reporter task completed prematurely")

            logger("XX waiting for runner to finish")
            await runner.finish()

            logger("XX gathering all tasks")
            await asyncio.gather(*all_tasks)

            logger("XX marking as complete")
            test_report.test_status.status = "completed"

        except Exception:
            test_report.test_status.status = "failed"
            raise

        finally:
            logger("XX Stopping the reporter")
            stop_reporter = True
            await reporter

    async def update_test_status(self, test_status):
        now = datetime.datetime.now()
        if test_status.start_time == datetime.datetime.min:
            test_status.start_time = now
        test_status.elapsed_time = now - test_status.start_time

        test_status.ops_failed = test_status.d2c.ops_failed

        # BKTODO: this returns the gc info for the pytest process.  move this to the process under test
        counts = gc.get_count()
        test_status.active_objects = counts[0] + counts[1] + counts[2]


@pytest.mark.testgroup_iothub_device_stress
@pytest.mark.describe("Device Client Long Run")
class TestDeviceClientLongHaul(LongHaulTest):
    @pytest.fixture
    def client(self, test_device):
        return test_device


@pytest.mark.testgroup_iothub_module_stress
@pytest.mark.describe("Device Client Long Run")
class TestModuleClientLongHaul(LongHaulTest):
    @pytest.fixture
    def client(self, test_module):
        return test_module
