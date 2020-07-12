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
    "testConfig": {
        "d2c": {"enabled": True, "intervalLength": 1, "opsPerInterval": 15},
        # "totalDuration": "00:00:10",
        "totalDuration": "72:00:10",
    }
}


async def _log_exception(aw):
    """
    Log any exceptions that happen while running this awaitable
    """
    try:
        await aw
    except Exception:
        logger("Exception raised")
        logger(traceback.format_exc())
        raise


def _get_seconds(interval):
    """
    Return interval duration in seconds.  Using this, we can author tests with either
    timedelta-based intervals, integers, or floats.
    """
    if isinstance(interval, datetime.timedelta):
        return interval.total_seconds()
    elif isinstance(interval, int) or isinstance(interval, float):
        return interval
    else:
        assert False


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
                    _log_exception(
                        asyncio.wait_for(self.run_one_op(), timeout=self.timeout)
                    )
                    for _ in range(0, self.ops_per_interval)
                ]
            )
        else:
            return set()

    @abc.abstractmethod
    async def run_one_op(self):
        pass

    async def stop(self):
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
            timeout=_get_seconds(test_config.timeout_interval),
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

        self.uncompleted_ops = set()
        self.uncompleted_ops_lock = threading.Lock()

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

            with self.uncompleted_ops_lock:
                self.uncompleted_ops.add(op_id)

            with self.count_sending, measure_send_latency:
                await self.do_send(op_id)

            with self.count_verifying, measure_verify_latency:
                await self.do_receive(op_id)

            with self.uncompleted_ops_lock:
                self.uncompleted_ops.remove(op_id)

            self.count_completed.increment()

        except Exception as e:
            logger("OP FAILED: Exception running op: {}".format(type(e)))
            self.count_failed.increment()


not_received = "not received"
received = "received"


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

        self.op_id_list = {}
        self.op_id_list_lock = threading.Lock()
        self.listener = None

    async def do_send(self, op_id):
        telemetry = make_message_payload()
        telemetry["op_id"] = op_id
        with self.op_id_list_lock:
            logger("setting op_id {} to not_received".format(op_id))
            self.op_id_list[op_id] = not_received
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
                op_id = message["op_id"]
                logger("received op_id {}".format(op_id))
                with self.op_id_list_lock:
                    if op_id in self.op_id_list:
                        if isinstance(self.op_id_list[op_id], asyncio.Future):
                            logger("Waiting for op_id {}.  signalling.".format(op_id))
                            self.op_id_list[op_id].set_result(True)
                        elif self.op_id_list[op_id] in [not_received, received]:
                            logger(
                                "not yet waiting for op_id {}.  Marking as received".format(
                                    op_id
                                )
                            )
                            self.op_id_list[op_id] = received
                        else:
                            logger(
                                "unexpected value in op_id_list for op_id {}: {}".format(
                                    op_id, self.op_id_list[op_id]
                                )
                            )
                            assert False
                    else:
                        logger("Received already-handled op_id {}".format(op_id))

    async def wait_for_completion(self, op_id):
        message_received = asyncio.Future()

        with self.op_id_list_lock:
            # if we've received it, return.  Else, set a future for the listener to complete when it does receive.
            if op_id in self.op_id_list:
                if self.op_id_list[op_id] == received:
                    logger("op_id {} already received.  returning".format(op_id))
                    return
                elif self.op_id_list[op_id] == not_received:
                    logger("op_id {} not received.  storing future".format(op_id))
                    self.op_id_list[op_id] = message_received
                else:
                    logger(
                        "unexpected value in op_id_list for op_id {}: {}".format(
                            op_id, self.op_id_list[op_id]
                        )
                    )
                    assert False
            else:
                logger("waiting for op_id which is not in op_id_list {}".format(op_id))
                assert False

            # see if the previous listener is done.
            if self.listener and self.listener.done():
                # call result() to force an exception if the listener had one
                logger(
                    "starting new listener.  Previous = {}".format(
                        self.listener.exception()
                    )
                )
                self.listener.result()
                self.listener = None

            # start a new future
            if self.listener is None:
                self.listener = asyncio.create_task(
                    _log_exception(self.listen_on_eventhub())
                )

        await message_received

    async def stop(self):
        if self.listener:
            self.listener.cancel()
            self.listener = None


class IntervalOperationUpdateTestReport(IntervalOperation):
    def __init__(
        self, *, test_config, test_status, longhaul_control_device, longhaul_ops
    ):
        super(IntervalOperationUpdateTestReport, self).__init__(
            interval_length=_get_seconds(test_config.reporting_interval),
            ops_per_interval=1,
            timeout=_get_seconds(test_config.timeout_interval),
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

    async def stop(self):
        # report one last time before we stop the test
        await self.run_one_op()


class IntervalOperationSendTestTelemetry(IntervalOperation):
    def __init__(
        self, *, test_config, test_status, longhaul_control_device, longhaul_ops
    ):
        super(IntervalOperationSendTestTelemetry, self).__init__(
            interval_length=_get_seconds(test_config.telemetry_interval),
            ops_per_interval=1,
            timeout=_get_seconds(test_config.timeout_interval),
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

    async def stop(self):
        # send one last time before we stop the test
        await self.run_one_op()


@six.add_metaclass(abc.ABCMeta)
class RobustListener(object):
    def __init__(self):
        self.listener_task = None

    async def start(self):
        logger("Starting {} listener".format(type(self)))
        assert not self.listener_task
        self.listener_task = asyncio.create_task(
            _log_exception(self.listener_function())
        )
        self.listener_task.add_done_callback(self.listener_done)

    def listener_done(self, task):
        self.restart_sync()

    def restart_sync(self):
        logger("Restarting {} listener".format(type(self)))
        self.listener_task = None
        asyncio.get_running_loop().run_until_complete(_log_exception(self.start()))

    @abc.abstractmethod
    async def listener_function(self):
        pass

    async def prevent_restart(self):
        if self.listener_task:
            self.listener_task.remove_done_callback(self.listener_done)

    async def wait_for_completion(self):
        if self.listener_task:
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
            self.listener_task = None

    async def stop(self):
        if self.listener_task:
            logger("Stopping {} listener".format(type(self)))
            self.prevent_restart()
            self.listener_task.cancel()
            self.wait_for_completion()


class CommandListener(RobustListener):
    def __init__(self, longhaul_control_device, coro):
        super(CommandListener, self).__init__()
        self.longhaul_control_device = longhaul_control_device
        self.coro = coro

    async def listener_function(self):
        logger("In listener function")
        while True:
            command = await self.longhaul_control_device.wait_for_c2d_message()
            logger("Listener received command {}".format(command.__dict__))
            if command.body == "stop":
                await self.prevent_restart()
                await self.coro()
                return

    async def stop(self):
        await self.prevent_restart()
        await self.coro()
        await self.wait_for_completion()
        self.longhaul_control_device = None
        self.coro = None


class IntervalOperationRenewEventhub(IntervalOperation):
    def __init__(self, *, test_config, eventhub):
        super(IntervalOperationRenewEventhub, self).__init__(
            interval_length=_get_seconds(test_config.eventhub_renew_interval),
            ops_per_interval=1,
            timeout=_get_seconds(test_config.timeout_interval),
        )
        self.eventhub = eventhub

    async def run_one_op(self):
        logger("renewing eventhub listener")
        await self.eventhub.start_new_listener()


class LongHaulTest(object):
    async def test_longhaul(
        self, client, eventhub, service, longhaul_control_device, caplog
    ):
        await eventhub.connect()

        test_config = DesiredTestProperties.from_dict(desired_node_config).test_config

        test_report = ReportedTestProperties()
        test_report.test_config = test_config
        test_status = test_report.test_status
        test_status.status = "running"

        stop = False

        async def set_stop_flag():
            nonlocal stop
            logger("stop = True")
            stop = True

        command_listener = CommandListener(longhaul_control_device, set_stop_flag)
        await command_listener.start()

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
        renew_eventhub = IntervalOperationRenewEventhub(
            test_config=test_config, eventhub=eventhub
        )

        all_ops = set(longhaul_ops.values()) | set(
            [update_test_report, send_test_telemetry, renew_eventhub]
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

            logger("Marking test as complete")
            test_report.test_status.status = "completed"

        except Exception:
            logger("Marking test as failed")
            traceback.print_exc()
            test_report.test_status.status = "failed"

            for op in longhaul_ops.values():
                if len(op.uncompleted_ops):
                    logger(
                        "{} has the following uncompleted op_id's: {}".format(
                            type(op), op.uncompleted_ops
                        )
                    )

            raise

        finally:
            # stop all of our longhaul ops, then stop our reporting ops.
            # order is important here since send_test_telemetry feeds data into
            # update_test_report.
            logger("Stopping command listener")
            await service.send_c2d(longhaul_control_device.device_id, "stop")
            await command_listener.stop()
            logger("stopping all  ops")
            await asyncio.gather(*(op.stop() for op in longhaul_ops.values()))
            logger("sending last telemetry and updating reported properties")
            await renew_eventhub.stop()
            await send_test_telemetry.stop()
            await update_test_report.stop()


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
