# Copyrigh (c Microsoft. All rights reserved.
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
import limitations

from longhaul_config import LonghaulConfig
from longhaul_telemetry import (
    PlatformProperties,
    LonghaulProperties,
    LonghaulD2cTelemetry,
    LonghaulTelemetry,
)
from measurement import (
    TrackCount,
    TrackAverage,
    MeasureRunningCodeBlock,
    MeasureLatency,
)
from horton_logging import logger
from sample_content import make_message_payload

pytestmark = pytest.mark.asyncio


longhaul_config = {
    "longhaulD2cEnabled": True,
    "LonghaulD2cIntervalLength": 1,
    "LonghaulD2cOpsPerInterval": 5,
    "LonghaulTotalDuration": "00:00:30",
    # "LonghaulTotalDuration": "72:00:10",
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

        self.next_op_id = TrackCount()

        self.count_sending = MeasureRunningCodeBlock("sending")
        self.count_verifying = MeasureRunningCodeBlock("verifying")

        self.total_count_completed = TrackCount()
        self.total_count_failed = TrackCount()

        self.average_send_latency = TrackAverage()
        self.average_verify_latency = TrackAverage()

        # BKTODO: do we need any locks in here?
        self.uncompleted_ops = set()
        self.uncompleted_ops_lock = threading.Lock()

    @abc.abstractmethod
    async def send_operation(self, op_id):
        pass

    @abc.abstractmethod
    async def verify_operation(self, op_id):
        pass

    async def run_one_op(self):
        try:
            measure_send_latency = MeasureLatency(tracker=self.average_send_latency)
            measure_verify_latency = MeasureLatency(tracker=self.average_verify_latency)

            op_id = self.next_op_id.increment()

            with self.uncompleted_ops_lock:
                self.uncompleted_ops.add(op_id)

            with self.count_sending, measure_send_latency:
                await self.send_operation(op_id)

            with self.count_verifying, measure_verify_latency:
                await self.verify_operation(op_id)

            with self.uncompleted_ops_lock:
                self.uncompleted_ops.remove(op_id)

            self.total_count_completed.increment()

        except Exception as e:
            logger("OP FAILED: Exception running op: {}".format(type(e)))
            logger(traceback.format_exc())
            self.total_count_failed.increment()


not_received = "not received"
received = "received"


class IntervalOperationD2c(IntervalOperationLonghaul):
    """
    Class represending the testing of D2C as a longhaul operation
    """

    def __init__(self, *, test_config, client, eventhub, longhaul_control_device):
        super(IntervalOperationD2c, self).__init__(
            test_config=test_config,
            interval_length=test_config.longhaul_d2c_interval_length,
            ops_per_interval=test_config.longhaul_d2c_ops_per_interval,
            longhaul_control_device=longhaul_control_device,
        )

        self.client = client
        self.eventhub = eventhub

        self.op_id_list = {}
        self.op_id_list_lock = threading.Lock()

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
        telemetry = LonghaulD2cTelemetry()

        telemetry.total_count_d2c_completed = self.total_count_completed.get_count()
        telemetry.total_count_d2c_failed = self.total_count_failed.get_count()
        telemetry.current_count_d2c_sending = self.count_sending.get_count()
        telemetry.current_count_d2c_verifying = self.count_verifying.get_count()
        telemetry.average_latency_d2c_send = self.average_send_latency.extract()
        telemetry.average_latency_d2c_verify = self.average_verify_latency.extract()

        logger("publishing {}".format(telemetry.to_dict()))
        await self.longhaul_control_device.send_event(telemetry.to_dict())

        if (
            self.total_count_failed.get_count()
            > self.test_config.longhaul_d2c_count_failures_allowed
        ):
            raise Exception(
                "D2c failures ({}) exceeeded amount allowed ({})".format(
                    self.total_count_failed.get_count(),
                    self.test_config.longhaul_d2c_count_failures_allowed,
                )
            )

    async def stop(self):
        if self.listener:
            self.listener.cancel()
            self.listener = None


class IntervalOperationUpdateLonghaulProperties(IntervalOperation):
    def __init__(self, *, test_config, execution_properties, longhaul_control_device):
        super(IntervalOperationUpdateLonghaulProperties, self).__init__(
            test_config=test_config,
            interval_length=_get_seconds(test_config.longhaul_property_update_interval),
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


class IntervalOperationSendLonghaulTelemetry(IntervalOperation):
    def __init__(
        self, *, test_config, client, system_control, longhaul_control_device, pid
    ):
        super(IntervalOperationSendLonghaulTelemetry, self).__init__(
            test_config=test_config,
            interval_length=_get_seconds(test_config.longhaul_telemetry_interval),
            ops_per_interval=1,
            longhaul_control_device=longhaul_control_device,
        )
        self.client = client
        self.pid = pid
        self.system_control = system_control
        self.last_voluntary_context_switches = 0
        self.last_nonvoluntary_context_switches = 0

    async def run_one_op(self):
        telemetry = LonghaulTelemetry()

        wrapper_stats = await self.client.settings.wrapper_api.get_wrapper_stats()
        system_stats = await self.system_control.get_system_stats(self.pid)

        telemetry.pytest_gc_object_count = len(gc.get_objects())

        telemetry.system_uptime_in_seconds = float(
            system_stats.get("system_uptime", "0.0")
        )
        telemetry.system_memory_free_in_kb = int(system_stats.get("system_MemFree", 0))
        telemetry.system_memory_available_in_kb = int(
            system_stats.get("system_MemAvailable", 0)
        )

        telemetry.process_gc_object_count = int(
            wrapper_stats.get("wrapperGcObjectCount", 0)
        )
        telemetry.process_virtual_memory_size_in_kb = int(
            system_stats.get("process_VmmSize", 0)
        )
        telemetry.process_resident_memory_in_kb = int(
            system_stats.get("process_VmRSS", 0)
        )
        telemetry.process_shared_memory_in_kb = int(
            system_stats.get("process_RssFile", 0)
        ) + int(system_stats.get("process.RssShmem", 0))

        voluntary_context_switches = int(
            system_stats.get("process_voluntary_ctxt_switches", 0)
        )
        nonvoluntary_context_switches = int(
            system_stats.get("process_nonvoluntary_ctxt_switches", 0)
        )

        telemetry.process_voluntary_context_switches_per_second = (
            voluntary_context_switches - self.last_voluntary_context_switches
        ) / self.interval_length
        telemetry.process_nonvoluntary_context_switches_per_second = (
            nonvoluntary_context_switches - self.last_nonvoluntary_context_switches
        ) / self.interval_length

        self.last_voluntary_context_switches = voluntary_context_switches
        self.last_nonvoluntary_context_switches = nonvoluntary_context_switches

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


async def set_platform_properties(*, client, longhaul_control_device, system_control):
    wrapper_stats = await client.settings.wrapper_api.get_wrapper_stats()
    system_stats = await system_control.get_system_stats(0)

    properties = PlatformProperties()
    properties.language = wrapper_stats.get("language", "")
    properties.language_version = wrapper_stats.get("languageVersion", "")

    properties.os = system_stats.get("osType", "")
    properties.os_release = system_stats.get("osRelease", "")
    properties.system_architecture = system_stats.get("systemArchitecture", "")

    properties.sdk_repo = system_stats.get("sdkRepo", "")
    properties.sdk_commit = system_stats.get("sdkCommit", "")
    properties.sdk_sha = system_stats.get("sdkSha", "")

    properties.test_hub_name = client.settings.iothub_host_name
    properties.test_device_id = client.device_id
    properties.test_module_id = getattr(client, "module_id", "")

    properties.system_memory_size_in_kb = int(system_stats.get("system_MemTotal", 0))

    patch = {"reported": properties.to_dict()}
    logger("reporting: {}".format(patch))
    await longhaul_control_device.patch_twin(patch)

    return wrapper_stats["wrapperPid"]


class LongHaulTest(object):
    async def test_longhaul(
        self, client, eventhub, longhaul_control_device, system_control, caplog
    ):
        await eventhub.connect()
        if limitations.needs_manual_connect(client):
            await client.connect2()

        test_config = LonghaulConfig.from_dict(longhaul_config)

        pid = await set_platform_properties(
            client=client,
            longhaul_control_device=longhaul_control_device,
            system_control=system_control,
        )

        start_time = datetime.datetime.now()

        execution_properties = LonghaulProperties()
        execution_properties.longhaul_status = "running"
        execution_properties.longhaul_start_time = start_time
        execution_properties.longhaul_elapsed_time = datetime.timedelta(0)

        # send initial execution properties
        patch = {"reported": execution_properties.to_dict()}
        logger("reporting: {}".format(patch))
        await longhaul_control_device.patch_twin(patch)

        # no need to send start time every time
        execution_properties.longhaul_start_time = (
            LonghaulProperties._defaults.longhaul_start_time
        )

        longhaul_ops = {
            "d2c": IntervalOperationD2c(
                test_config=test_config,
                client=client,
                eventhub=eventhub,
                longhaul_control_device=longhaul_control_device,
            )
        }
        update_test_report = IntervalOperationUpdateLonghaulProperties(
            test_config=test_config,
            execution_properties=execution_properties,
            longhaul_control_device=longhaul_control_device,
        )
        send_execution_telemetry = IntervalOperationSendLonghaulTelemetry(
            test_config=test_config,
            longhaul_control_device=longhaul_control_device,
            client=client,
            system_control=system_control,
            pid=pid,
        )

        all_ops = set(longhaul_ops.values()) | set(
            [update_test_report, send_execution_telemetry]
        )

        try:
            one_second = 1.0
            all_tasks = set()

            while (
                execution_properties.longhaul_elapsed_time
                < test_config.longhaul_total_duration
                or execution_properties.longhaul_elapsed_time == datetime.timedelta(0)
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

                execution_properties.longhaul_elapsed_time = (
                    datetime.datetime.now() - start_time
                )

            await asyncio.gather(*all_tasks)

            logger("Marking test as complete")
            execution_properties.longhaul_status = "completed"

        except Exception:
            logger("Marking test as failed")
            logger(traceback.format_exc())
            execution_properties.longhaul_status = "failed"

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
            # order is important here since send_execution_telemetry feeds data into
            # update_test_report.
            logger("stopping all  ops")
            await asyncio.gather(*(op.stop() for op in longhaul_ops.values()))
            logger("sending last telemetry and updating reported properties")
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
