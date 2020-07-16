# Copyrigh (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest
import json
import gc
import threading
import six
import abc
import datetime
import traceback

from longhaul_config import LonghaulConfig
from longhaul_telemetry import (
    PlatformProperties,
    ExecutionProperties,
    D2cTelemetry,
    ExecutionTelemetry,
)
from measurement import (
    TrackCount,
    TrackMax,
    MeasureRunningCodeBlock,
    MeasureLatency,
    NoLock,
)
from horton_logging import logger
from sample_content import make_message_payload

pytestmark = pytest.mark.asyncio

# BKTODO:
# add events for connected, disconnected
# change stop to a function


longhaul_config = {
    "d2cEnabled": True,
    "d2cIntervalLength": 1,
    "d2cOpsPerInterval": 15,
    "TotalDuration": "00:00:30",
    # "totalDuration": "72:00:10",
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

    def __init__(
        self, *, test_config, interval_length, ops_per_interval, longhaul_control_device
    ):
        self.test_config = test_config
        self.interval_length = interval_length
        self.ops_per_interval = ops_per_interval
        self.longhaul_control_device = longhaul_control_device
        self.interval_index = 0

    async def schedule_one_second(self):
        self.interval_index += 1
        if self.interval_index == self.interval_length:
            self.interval_index = 0

            await self.send_operation_telemetry()

            return set(
                [
                    _log_exception(
                        asyncio.wait_for(
                            self.run_one_op(),
                            timeout=_get_seconds(self.test_config.timeout_interval),
                        )
                    )
                    for _ in range(0, self.ops_per_interval)
                ]
            )
        else:
            return set()

    @abc.abstractmethod
    async def run_one_op(self):
        pass

    async def send_operation_telemetry(self):
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

    def __init__(self, *args, **kwargs):
        super(IntervalOperationLonghaul, self).__init__(*args, **kwargs)

        self.next_op_id = TrackCount(use_lock=False)

        self.count_sending = MeasureRunningCodeBlock(
            "sending", logger=None, use_lock=False
        )
        self.count_verifying = MeasureRunningCodeBlock(
            "verifying", logger=None, use_lock=False
        )

        self.count_total_completed = TrackCount(use_lock=False)
        self.count_total_failed = TrackCount(use_lock=False)

        self.track_max_send_latency = TrackMax(use_lock=False)
        self.track_max_verify_latency = TrackMax(use_lock=False)

        self.uncompleted_ops = set()
        self.uncompleted_ops_lock = NoLock() or threading.Lock()

    @abc.abstractmethod
    async def send_operation(self, op_id):
        pass

    @abc.abstractmethod
    async def verify_operation(self, op_id):
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
                await self.send_operation(op_id)

            with self.count_verifying, measure_verify_latency:
                await self.verify_operation(op_id)

            with self.uncompleted_ops_lock:
                self.uncompleted_ops.remove(op_id)

            self.count_total_completed.increment()

        except Exception as e:
            logger("OP FAILED: Exception running op: {}".format(type(e)))
            self.count_failed.increment()


not_received = "not received"
received = "received"


class IntervalOperationD2c(IntervalOperationLonghaul):
    """
    Class represending the testing of D2C as a longhaul operation
    """

    def __init__(self, *, test_config, client, eventhub, longhaul_control_device):
        super(IntervalOperationD2c, self).__init__(
            test_config=test_config,
            interval_length=test_config.d2c_interval_length,
            ops_per_interval=test_config.d2c_ops_per_interval,
            longhaul_control_device=longhaul_control_device,
        )

        self.client = client
        self.eventhub = eventhub

        self.op_id_list = {}
        self.op_id_list_lock = NoLock() or threading.Lock()

        self.listener = None

    async def send_operation(self, op_id):
        telemetry = make_message_payload()
        telemetry["op_id"] = op_id
        with self.op_id_list_lock:
            logger("setting op_id {} to not_received".format(op_id))
            self.op_id_list[op_id] = not_received
        await self.client.send_event(telemetry)

    async def verify_operation(self, op_id):
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
                            if self.op_id_list[op_id].done():
                                logger(
                                    "Waiting for op_id {}.  already signalled.  doing nothing.".format(
                                        op_id
                                    )
                                )
                            else:
                                logger(
                                    "Waiting for op_id {}.  signalling.".format(op_id)
                                )
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

    async def send_operation_telemetry(self):
        telemetry = D2cTelemetry()

        telemetry.count_total_d2c_completed = self.count_total_completed.get_count()
        telemetry.count_total_d2c_failed = self.count_total_failed.get_count()
        telemetry.count_current_d2c_sending = self.count_sending.get_count()
        telemetry.count_current_d2c_verifying = self.count_verifying.get_count()
        telemetry.latency_d2c_send = self.track_max_send_latency.extract()
        telemetry.latency_d2c_verify = self.track_max_verify_latency.extract()

        await self.longhaul_control_device.send_event(telemetry.to_dict())

        if (
            self.count_total_failed.get_count()
            > self.test_config.d2c_count_failures_allowed
        ):
            raise Exception(
                "D2c failures ({}) exceeeded amount allowed ({})".format(
                    self.count_total_failed.get_count(),
                    self.test_config.d2c_count_failures_allowed,
                )
            )

    async def stop(self):
        if self.listener:
            self.listener.cancel()
            self.listener = None


class IntervalOperationUpdateExecutionProperties(IntervalOperation):
    def __init__(self, *, test_config, execution_properties, longhaul_control_device):
        super(IntervalOperationUpdateExecutionProperties, self).__init__(
            test_config=test_config,
            interval_length=_get_seconds(test_config.property_update_interval),
            ops_per_interval=1,
            longhaul_control_device=longhaul_control_device,
        )
        self.execution_properties = execution_properties

    async def run_one_op(self):

        patch = {"reported": self.execution_properties.to_dict()}
        logger("reporting: {}".format(patch))
        await self.longhaul_control_device.patch_twin(patch)

    async def stop(self):
        # report one last time before we stop the test
        await self.run_one_op()


class IntervalOperationSendExecutionTelemetry(IntervalOperation):
    def __init__(
        self, *, test_config, client, system_control, longhaul_control_device, pid
    ):
        super(IntervalOperationSendExecutionTelemetry, self).__init__(
            test_config=test_config,
            interval_length=_get_seconds(test_config.telenetry_interval),
            ops_per_interval=1,
            longhaul_control_device=longhaul_control_device,
        )
        self.client = client
        self.pid = pid
        self.system_control = system_control

    async def run_one_op(self):
        telemetry = ExecutionTelemetry()

        wrapper_stats = await self.client.settings.wrapper_api.get_wrapper_stats()
        system_stats = await self.system_control.get_system_stats(self.pid)

        telemetry.pytest_gc_object_count = len(gc.get_objects())

        self.system_uptime = float(system_stats.get("system_uptime", "0.0"))
        self.system_memory_size = int(system_stats.get("system_MemTotal", 0))
        self.system_memory_free = int(system_stats.get("system_MemFree", 0))
        self.system_memory_available = int(system_stats.get("system_MemAvailable", 0))

        self.process_gc_object_count = int(wrapper_stats.get("wrapperGcObjectCount", 0))
        self.process_virtual_memory_size = int(system_stats.get("process_VmmSize", 0))
        self.process_resident_memory = int(system_stats.get("process_VmRSS", 0))
        self.process_shared_memory = int(system_stats.get("process_RssFile", 0)) + int(
            system_stats.get("process.RssShmem", 0)
        )
        self.process_voluntary_context_switches = int(
            system_stats.get("process_voluntary_ctxt_switches", 0)
        )
        self.process_nonvoluntary_contexxt_switches = int(
            system_stats.get("process_nonvoluntary_ctxt_switches", 0)
        )

        logger("publishing: {}".format((telemetry.to_dict())))
        await self.longhaul_control_device.send_event(telemetry.to_dict())

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
    def __init__(self, *, test_config, eventhub, longhaul_control_device):
        super(IntervalOperationRenewEventhub, self).__init__(
            test_config=test_config,
            interval_length=_get_seconds(test_config.eventhub_renew_interval),
            ops_per_interval=1,
            longhaul_control_device=longhaul_control_device,
        )
        self.eventhub = eventhub

    async def run_one_op(self):
        logger("renewing eventhub listener")
        await self.eventhub.start_new_listener()


async def set_platform_properties(*, client, longhaul_control_device):
    stats = await client.settings.wrapper_api.get_wrapper_stats()

    properties = PlatformProperties()
    properties.os = stats["osType"]
    properties.os_release = stats["osRelease"]
    properties.system_architecture = stats["systemArchitecture"]
    properties.language = stats["language"]
    properties.language_version = stats["languageVersion"]
    properties.sdk_repo = stats["sdkRepo"]
    properties.sdk_commit = stats["sdkCommit"]
    properties.sdk_sha = stats["sdkSha"]

    patch = {"reported": properties.to_dict()}
    logger("reporting: {}".format(patch))
    await longhaul_control_device.patch_twin(patch)

    return stats["wrapperPid"]


class LongHaulTest(object):
    async def test_longhaul(
        self, client, eventhub, service, longhaul_control_device, system_control, caplog
    ):
        await eventhub.connect()

        test_config = LonghaulConfig.from_dict(longhaul_config)

        pid = await set_platform_properties(
            client=client, longhaul_control_device=longhaul_control_device
        )

        execution_properties = ExecutionProperties()
        execution_properties.execution_status = "new"
        execution_properties.execution_start_time = datetime.datetime.now()
        execution_properties.execution_elapsed_time = datetime.timedelta(0)

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
                client=client,
                eventhub=eventhub,
                longhaul_control_device=longhaul_control_device,
            )
        }
        update_test_report = IntervalOperationUpdateExecutionProperties(
            test_config=test_config,
            execution_properties=execution_properties,
            longhaul_control_device=longhaul_control_device,
        )
        send_execution_telemetry = IntervalOperationSendExecutionTelemetry(
            test_config=test_config,
            longhaul_control_device=longhaul_control_device,
            client=client,
            system_control=system_control,
            pid=pid,
        )
        renew_eventhub = IntervalOperationRenewEventhub(
            test_config=test_config,
            eventhub=eventhub,
            longhaul_control_device=longhaul_control_device,
        )

        all_ops = set(longhaul_ops.values()) | set(
            [update_test_report, send_execution_telemetry, renew_eventhub]
        )

        try:
            one_second = 1.0
            all_tasks = set()

            while not stop and (
                execution_properties.execution_elapsed_time < test_config.total_duration
                or execution_properties.execution_elapsed_time == datetime.timedelta(0)
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

                        all_tasks = pending

                        if len(all_tasks) == 0:
                            await asyncio.sleep(one_second - wait_time.get_latency())

                execution_properties.execution_elapsed_time = (
                    datetime.datetime.now() - execution_properties.execution_start_time
                )

            await asyncio.gather(*all_tasks)

            logger("Marking test as complete")
            execution_properties.execution_status = "completed"

        except Exception:
            logger("Marking test as failed")
            logger(traceback.format_exc())
            execution_properties.execution_status = "failed"

            for op in longhaul_ops.values():
                if len(op.uncompleted_ops):
                    logger(
                        "{} has the following uncompleted op_id's: {}".format(
                            type(op), op.uncompleted_ops
                        )
                    )

            raise

        finally:
            logger("Stopping command listener")
            await service.send_c2d(longhaul_control_device.device_id, "stop")
            await command_listener.stop()

            # stop all of our longhaul ops, then stop our reporting ops.
            # order is important here since send_execution_telemetry feeds data into
            # update_test_report.
            logger("stopping all  ops")
            await asyncio.gather(*(op.stop() for op in longhaul_ops.values()))
            logger("sending last telemetry and updating reported properties")
            await renew_eventhub.stop()
            await send_execution_telemetry.stop()
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
