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
import traceback

from longhaul_config import (
    DesiredTestProperties,
    ReportedTestProperties,
    IntervalReport,
)
from measurement import TrackCount, TrackMax, MeasureRunningCodeBlock, MeasureLatency
from horton_logging import logger
from sample_content import make_message_payload

pytestmark = pytest.mark.asyncio

# BKTODO:
# add control to stop test
# add events for connected, disconnected
#


desired_node_config = {
    "test_config": {
        "d2c": {"enabled": True, "interval_length": 1, "ops_per_interval": 10},
        "total_duration": "0:00:30",
    }
}


@six.add_metaclass(abc.ABCMeta)
class IntervalOperation(object):
    """
    Class represending an operation run at some regular interval.  This class takes
    care of scheduling the individual operations according to the cadence specified in the
    constructor parameters
    """

    def __init__(self, *, interval_length, ops_per_interval, timeout):

        self.interval_length = interval_length
        self.ops_per_interval = ops_per_interval
        self.interval_index = 0
        self.timeout = timeout

    async def schedule_one_second(self):
        self.interval_index += 1
        if self.interval_index == self.interval_length:
            self.interval_index = 0

            return set(
                [
                    asyncio.wait_for(self.run_one_op(), timeout=self.timeout)
                    for _ in range(0, self.ops_per_interval)
                ]
            )
        else:
            return set()

    @abc.abstractmethod
    async def run_one_op(self):
        pass

    async def finish(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class IntervalOperationLonghaul(IntervalOperation):
    """
    Class represending a longhaul operation run at a regular interval.  This object breaks an
    operation into a "send" and a "receive" portion.  It also records data points about the operation
    for reporting, including counts and latency values.
    """

    def __init__(self, *, test_config, test_status, op_config):
        super(IntervalOperationLonghaul, self).__init__(
            interval_length=op_config.interval_length,
            ops_per_interval=op_config.ops_per_interval,
            timeout=test_config.timeout_interval.total_seconds(),
        )

        self.test_config = test_config
        self.test_status = test_status

        self.next_op_id = TrackCount()

        self.count_sending = MeasureRunningCodeBlock("sending", logger=None)
        self.count_verifying = MeasureRunningCodeBlock("verifying", logger=None)

        self.count_completed = TrackCount()
        self.count_failed = TrackCount()

        self.track_max_send_latency = TrackMax()
        self.track_max_verify_latency = TrackMax()

    @abc.abstractmethod
    async def do_send(self, op_id):
        pass

    @abc.abstractmethod
    async def do_receive(self, op_id):
        pass

    async def run_one_op(self):
        try:
            measure_send_latency = MeasureLatency(tracker=self.track_max_send_latency)
            measure_verify_latency = MeasureLatency(
                tracker=self.track_max_verify_latency
            )

            op_id = self.next_op_id.increment()

            with self.count_sending, measure_send_latency:
                await self.do_send(op_id)

            with self.count_verifying, measure_verify_latency:
                await self.do_receive(op_id)

            self.count_completed.increment()

        except Exception as e:
            logger("OP FAILED: Exception running op: {}".format(e))
            traceback.print_exc()
            self.count_failed.increment()


class IntervalOperationD2c(IntervalOperationLonghaul):
    """
    Class represending the testing of D2C as a longhaul operation
    """

    def __init__(self, *, test_config, test_status, client, eventhub):
        super(IntervalOperationD2c, self).__init__(
            test_config=test_config, test_status=test_status, op_config=test_config.d2c
        )

        self.client = client
        self.eventhub = eventhub

        self.mid_list = {}
        self.mid_list_lock = threading.Lock()
        self.listener = None

    async def do_send(self, op_id):
        telemetry = make_message_payload()
        telemetry["op_id"] = op_id
        await self.client.send_event(telemetry)

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


class IntervalOperationUpdateTestReport(IntervalOperation):
    def __init__(
        self, *, test_config, test_status, longhaul_control_device, longhaul_ops
    ):
        super(IntervalOperationUpdateTestReport, self).__init__(
            interval_length=test_config.reporting_interval.total_seconds(),
            ops_per_interval=1,
            timeout=test_config.timeout_interval.total_seconds(),
        )

        self.longhaul_control_device = longhaul_control_device
        self.longhaul_ops = longhaul_ops
        self.test_config = test_config
        self.test_status = test_status

        self.test_report = ReportedTestProperties()
        self.test_report.test_config = test_config
        self.test_report.test_status = test_status

    async def run_one_op(self):
        now = datetime.datetime.now()
        if self.test_status.start_time == datetime.datetime.min:
            self.test_status.start_time = now

        self.test_status.elapsed_time = now - self.test_status.start_time

        total_ops_failed = 0
        for op_name in self.longhaul_ops:
            op = self.longhaul_ops[op_name]
            op_status = getattr(self.test_status, op_name)

            op_status.ops_sending = op.count_sending.get_count()
            op_status.ops_verifying = op.count_verifying.get_count()

            total_ops_failed += op_status.ops_failed

        self.test_status.total_ops_failed = total_ops_failed

        patch = {"reported": self.test_report.to_dict()}
        logger("reporting: {}".format(patch))
        await self.longhaul_control_device.patch_twin(patch)

    async def finish(self):
        # report one last time before we finish the test
        await self.run_one_op()


class IntervalOperationSendTestTelemetry(IntervalOperation):
    def __init__(
        self, *, test_config, test_status, longhaul_control_device, longhaul_ops
    ):
        super(IntervalOperationSendTestTelemetry, self).__init__(
            interval_length=test_config.telemetry_interval.total_seconds(),
            ops_per_interval=1,
            timeout=test_config.timeout_interval.total_seconds(),
        )
        self.longhaul_control_device = longhaul_control_device
        self.longhaul_ops = longhaul_ops
        self.test_config = test_config
        self.test_status = test_status
        self.next_interval_id = TrackCount()

    async def run_one_op(self):
        telemetry = IntervalReport()

        telemetry.interval_id = self.next_interval_id.increment()
        telemetry.objects_in_pytest_process = len(gc.get_objects())

        # for each op, pull out the info since the last interval to send it up in
        # a telemetry message.  This is "what has happened since the last telemetry message"
        for op_name in self.longhaul_ops:
            op = self.longhaul_ops[op_name]
            op_status = getattr(telemetry, op_name)

            op_status.ops_completed = op.count_completed.extract()
            op_status.ops_failed = op.count_failed.extract()
            op_status.ops_sending = op.count_sending.get_count()
            op_status.ops_verifying = op.count_verifying.get_count()
            op_status.max_send_latency = op.track_max_send_latency.extract()
            op_status.max_verify_latency = op.track_max_verify_latency.extract()

        await self.longhaul_control_device.send_event(telemetry.to_dict())

        # Then, once we've sent it up as telemetry, add it to the test_status object where
        # we record stats since the beginning of the run.
        for op_name in self.longhaul_ops:
            op_status = getattr(telemetry, op_name)
            total_op_status = getattr(self.test_status, op_name)

            total_op_status.ops_completed += op_status.ops_completed
            total_op_status.ops_failed += op_status.ops_failed

    async def finish(self):
        # send one last time before we finish the test
        await self.run_one_op()


class LongHaulTest(object):
    async def listen_for_commands(self, longhaul_control_device, callback):
        while True:
            logger("listening")
            command = await longhaul_control_device.wait_for_c2d_message()
            if command.body == "stop":
                asyncio.ensure_future(callback())

    async def test_longhaul(self, client, eventhub, longhaul_control_device, caplog):
        await eventhub.connect()

        test_config = DesiredTestProperties.from_dict(desired_node_config).test_config

        test_report = ReportedTestProperties()
        test_report.test_config = test_config
        test_status = test_report.test_status
        test_status.status = "running"

        stop = False

        async def set_stop_flag():
            nonlocal stop
            stop = True

        # BKTODO: make more robust, probably following eventhub example from other machine
        command_listener = asyncio.ensure_future(
            self.listen_for_commands(longhaul_control_device, set_stop_flag)
        )

        longhaul_ops = {
            "d2c": IntervalOperationD2c(
                test_config=test_config,
                test_status=test_status,
                client=client,
                eventhub=eventhub,
            )
        }
        update_test_report = IntervalOperationUpdateTestReport(
            test_config=test_config,
            test_status=test_status,
            longhaul_control_device=longhaul_control_device,
            longhaul_ops=longhaul_ops,
        )
        send_test_telemetry = IntervalOperationSendTestTelemetry(
            test_config=test_config,
            test_status=test_status,
            longhaul_control_device=longhaul_control_device,
            longhaul_ops=longhaul_ops,
        )

        all_ops = set(longhaul_ops.values()) | set(
            [update_test_report, send_test_telemetry]
        )

        try:
            one_second = 1
            all_tasks = set()

            while not stop and (
                test_status.elapsed_time < test_config.total_duration
                or test_status.elapsed_time == datetime.timedelta(0)
            ):
                # pytest caches all messages.  We don't want that, but I couldn't find a way
                # to turn it off, so we just clear it once a second.
                caplog.clear()

                if command_listener.done():
                    listener = command_listener
                    listener = None
                    listener.result()  # raises if there's an error
                    raise Exception("command listener unexpectedly stopped")

                for op in all_ops:
                    all_tasks.update(await op.schedule_one_second())

                wait_time = MeasureLatency()
                with wait_time:
                    while len(all_tasks) and wait_time.get_latency() < one_second:
                        done, pending = await asyncio.wait(
                            all_tasks,
                            timeout=one_second,
                            return_when=asyncio.FIRST_EXCEPTION,
                        )

                        await asyncio.gather(*done)

                        if (
                            test_status.total_ops_failed
                            > test_config.max_allowed_failures
                        ):
                            raise Exception("failure count exceeded maximum allowed")

                        all_tasks = pending

                    if len(all_tasks) == 0:
                        await asyncio.sleep(one_second - wait_time.get_latency())

            await asyncio.gather(*all_tasks)

            test_report.test_status.status = "completed"

        except Exception:
            test_report.test_status.status = "failed"
            raise

        finally:
            # finish all of our longhaul ops, then finish our reporting ops.
            # order is important here since send_test_telemetry feeds data into
            # update_test_report.
            if command_listener:
                try:
                    command_listener.cancel()
                    await command_listener
                except asyncio.CancelledError:
                    pass
            await asyncio.gather(*(op.finish() for op in longhaul_ops.values()))
            await send_test_telemetry.finish()
            await update_test_report.finish()


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
