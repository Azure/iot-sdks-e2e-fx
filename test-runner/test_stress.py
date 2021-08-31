# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import datetime
import random
import sample_content
from adapters import adapter_config
from twin_tests import (
    patch_desired_props,
    wait_for_desired_properties_patch,
    wait_for_reported_properties_update,
)
from method_tests import run_method_call_test
from horton_logging import logger

pytestmark = pytest.mark.asyncio

# how long to test for
test_run_time = datetime.timedelta(days=0, hours=2, minutes=0)

# maximum extra time to add to timeout.
max_timeout_overage = datetime.timedelta(minutes=15)

# actual timeout overage
timeout_overage = min(max_timeout_overage, test_run_time)

# actual timeout
test_timeout = (test_run_time + timeout_overage).total_seconds()

# number of times to repeat each operation (initial)
initial_repeats = 8

# number of times to repeat each operation (max)
max_repeats = 32

# random seed
random_seed = 2251226 + 1

# disconnect frequency in seconds.  This defines lower and upper bounds for how often to disconnect
disconnect_frequency = (5, 15)

# disconnect duration in seconds.  This defines lower and upper bounds for how long to remain disconnected
disconnect_duration = (5, 15)

# Amount of time to wait for any particular API to complete
api_timeout = 900

dashes = "".join(("-" for _ in range(0, 30)))


class StressTestConfig(object):
    test_telemetry = True
    test_handle_method = False
    test_invoke_module_method = False
    test_invoke_device_method = False
    test_desired_property_patch = True
    test_get_twin = True
    test_reported_properties = True


def pretty_time(t):
    """
    return pretty string for datetime and timedelta objects (no date, second accuracy)
    """
    if isinstance(t, datetime.timedelta):
        return str(datetime.timedelta(days=t.days, seconds=t.seconds))
    else:
        return t.strftime("%H:%M:%S")


class TimeLimit(object):
    def __init__(self, test_run_time):
        self.test_run_time = test_run_time
        self.test_start_time = datetime.datetime.now()
        self.test_end_time = self.test_start_time + self.test_run_time
        self.prefix = ""
        self.next_change = datetime.datetime.max
        self.error = None

    def is_test_done(self):
        if self.error:
            raise self.error

        logger(
            "{}: Change in {},  Remaining Time: {}".format(
                self.prefix,
                pretty_time(self.next_change - datetime.datetime.now()),
                pretty_time(self.test_end_time - datetime.datetime.now()),
            )
        )
        return datetime.datetime.now() >= self.test_end_time

    def print_progress(self):
        now = datetime.datetime.now()
        logger("Start time: {}".format(pretty_time(self.test_start_time)))
        logger("Duration:   {}".format(pretty_time(self.test_run_time)))
        logger("End time:   {}".format(pretty_time(self.test_end_time)))
        logger("now:        {}".format(pretty_time(now)))
        logger("Time left:  {}".format(pretty_time(self.test_end_time - now)))


class StressTest(object):
    @pytest.mark.skip(reason="")
    @pytest.mark.it("Run for {}".format(pretty_time(test_run_time)))
    async def test_stress(
        self, client, eventhub, service, registry, friend, leaf_device, system_control
    ):

        adapter_config.default_api_timeout = api_timeout

        random.seed(random.seed)

        await client.connect2()
        await client.disconnect2()

        time_limit = TimeLimit(test_run_time)

        async def chaos_function():
            nonlocal time_limit
            try:
                while True:
                    t = random.randrange(*disconnect_frequency)
                    logger("CHAOS: sleeping while connected for {} seconds".format(t))
                    time_limit.prefix = "connected for {}".format(
                        pretty_time(datetime.timedelta(seconds=t))
                    )
                    time_limit.next_change = datetime.datetime.now() + datetime.timedelta(
                        seconds=t
                    )
                    await asyncio.sleep(t)

                    logger("CHAOS: disconnecting")
                    await system_control.disconnect_network(
                        random.choice(["DROP", "REJECT"])
                    )

                    t = random.randrange(*disconnect_duration)
                    time_limit.prefix = "disconnected for {}".format(
                        pretty_time(datetime.timedelta(seconds=t))
                    )
                    time_limit.next_change = datetime.datetime.now() + datetime.timedelta(
                        seconds=t
                    )
                    logger(
                        "CHAOS: sleeping while disconnected for {} seconds".format(t)
                    )
                    await asyncio.sleep(t)

                    logger("CHAOS: reconnecting")
                    await system_control.reconnect_network()

            except asyncio.CancelledError as e:
                logger("Chaos function stopped because test is complete")
                time_limit.error = e

            except Exception as e:
                logger("chaos_function stopped because of {}: {}".format(type(e), e))
                time_limit.error = e

            finally:
                logger("CHAOS: final reconnect")
                await system_control.reconnect_network()

        chaos_future = asyncio.ensure_future(chaos_function())

        count = initial_repeats

        while count <= max_repeats:
            logger(dashes)
            logger("Next Iteration. Running with {} operations per step".format(count))
            time_limit.print_progress()
            logger(dashes)

            if StressTestConfig.test_telemetry:
                await self.do_test_telemetry(
                    client=client, eventhub=eventhub, count=count, time_limit=time_limit
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            if StressTestConfig.test_handle_method:
                await self.do_test_handle_method_from_service(
                    client=client, service=service, count=count, time_limit=time_limit
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            if StressTestConfig.test_invoke_module_method:
                await self.do_test_handle_method_to_friend(
                    client=client, friend=friend, count=count, time_limit=time_limit
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            if StressTestConfig.test_invoke_device_method:
                await self.do_test_handle_method_to_leaf_device(
                    client=client,
                    leaf_device=leaf_device,
                    count=count,
                    time_limit=time_limit,
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            if StressTestConfig.test_desired_property_patch:
                await self.do_test_desired_property_patch(
                    client=client, registry=registry, count=count, time_limit=time_limit
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            if StressTestConfig.test_get_twin:
                await self.do_test_get_twin(
                    client=client, registry=registry, count=count, time_limit=time_limit
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            if StressTestConfig.test_reported_properties:
                await self.do_test_reported_properties(
                    client=client, registry=registry, count=count, time_limit=time_limit
                )

                if time_limit.is_test_done():
                    chaos_future.cancel()
                    return

            count = count * 2

            if count > max_repeats:
                count = initial_repeats

    async def do_test_telemetry(self, *, client, eventhub, count, time_limit):
        logger("testing telemetry with {} operations".format(count))

        payloads = [sample_content.make_message_payload() for x in range(0, count)]
        futures = []

        # start listening before we send
        await eventhub.connect()
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id)
        )

        for payload in payloads:
            futures.append(asyncio.ensure_future(client.send_event(payload)))

        # wait for the send to complete, and verify that it arrvies
        await asyncio.gather(*futures)

        logger("All messages sent.  Awaiting reception")

        while len(payloads):
            received_message = await received_message_future

            if received_message in payloads:
                payloads.remove(received_message)
                logger(
                    "Received expected message: {},  {}/{} left".format(
                        received_message, len(payloads), count
                    )
                )
            else:
                logger("Received unexpected message: {}".format(received_message))

            if time_limit.is_test_done():
                await eventhub.disconnect()
                return

            if len(payloads):
                received_message_future = asyncio.ensure_future(
                    eventhub.wait_for_next_event(client.device_id)
                )

        await eventhub.disconnect()

    async def do_test_get_twin(self, *, client, registry, count, time_limit):
        await client.enable_twin()

        for i in range(0, count):
            if time_limit.is_test_done():
                return

            logger("get_twin {}/{}".format(i + 1, count))
            twin_sent = sample_content.make_desired_props()

            await patch_desired_props(registry, client, twin_sent)

            while True:
                twin_received = await client.get_twin()

                logger("twin sent:    " + str(twin_sent))
                logger("twin received:" + str(twin_received))
                if twin_sent["desired"]["foo"] == twin_received["desired"]["foo"]:
                    break
                else:
                    logger("Twin does not match.  Sleeping for 2 seconds and retrying.")
                    await asyncio.sleep(2)

    async def patch_desired(self, *, client, registry, mistakes=1):
        twin_sent = sample_content.make_desired_props()
        logger("Patching desired properties to {}".format(twin_sent))

        patch_future = asyncio.ensure_future(
            wait_for_desired_properties_patch(
                client=client, expected_twin=twin_sent, mistakes=mistakes
            )
        )
        await asyncio.sleep(1)  # wait for async call to take effect

        await patch_desired_props(registry, client, twin_sent)

        await patch_future  # raises if patch not received

    async def do_test_desired_property_patch(
        self, *, client, registry, count, time_limit
    ):
        await client.enable_twin()

        # flush the desired property queue.  This is mostly removing
        # patches from previous get_twin tests, so we set mistakes to a large
        # number
        await self.patch_desired(
            client=client, registry=registry, mistakes=max_repeats * 2
        )

        for i in range(0, count):
            if time_limit.is_test_done():
                return

            logger("desired_property_patch {}/{}".format(i + 1, count))
            await self.patch_desired(client=client, registry=registry)
            logger("patch {} received".format(i))

    async def do_test_reported_properties(self, *, client, registry, count, time_limit):
        await client.enable_twin()

        for i in range(0, count):
            if time_limit.is_test_done():
                return

            logger("reported_properties {}/{}".format(i + 1, count))

            properties_sent = sample_content.make_reported_props()

            await client.patch_twin(properties_sent)

            await wait_for_reported_properties_update(
                properties_sent=properties_sent, client=client, registry=registry
            )

    async def do_test_handle_method_from_service(
        self, *, client, service, count, time_limit
    ):

        for i in range(0, count):
            if time_limit.is_test_done():
                return

            logger("method_from_service {}/{}".format(i + 1, count))

            # BKTODO: pull enable_methods out of run_method_call_test

            await run_method_call_test(source=service, destination=client)

    async def do_test_handle_method_to_friend(
        self, *, client, friend, count, time_limit
    ):

        for i in range(0, count):
            if time_limit.is_test_done():
                return

            logger("method_to_friend {}/{}".format(i + 1, count))

            await run_method_call_test(source=client, destination=friend)

    async def do_test_handle_method_to_leaf_device(
        self, *, client, leaf_device, count, time_limit
    ):

        for i in range(0, count):
            if time_limit.is_test_done():
                return

            logger("method_to_leaf_device {}/{}".format(i + 1, count))

            # BKTODO: pull enable_methods out of run_method_call_test

            await run_method_call_test(source=client, destination=leaf_device)


@pytest.mark.skip(reason="")
@pytest.mark.testgroup_edgehub_module_stress
@pytest.mark.testgroup_iothub_module_stress
@pytest.mark.describe("Module Client Stress")
@pytest.mark.timeout(test_timeout)
class _TestModuleClient2HourStress(StressTest):
    @pytest.fixture
    def client(self, test_module):
        return test_module


@pytest.mark.skip(reason="")
@pytest.mark.testgroup_iothub_device_stress
@pytest.mark.describe("Device Client Stress")
@pytest.mark.timeout(test_timeout)
class _TestDeviceClient2HourStress(StressTest):
    @pytest.fixture
    def client(self, test_device):
        return test_device
