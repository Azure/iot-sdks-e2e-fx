# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import datetime
from utilities import next_random_string
from twin_tests import (
    patch_desired_props,
    wait_for_desired_properties_patch,
    wait_for_reported_properties_update,
)
from method_tests import run_method_call_test

pytestmark = pytest.mark.asyncio

# how long to test for
test_run_time = datetime.timedelta(days=0, hours=2, minutes=0)

# maximum extra time to add to timeout.  used to complete current iteration.
max_timeout_overage = datetime.timedelta(minutes=30)

# actual timeout overage
timeout_overage = min(max_timeout_overage, test_run_time)

# actual timeout
test_timeout = (test_run_time + timeout_overage).total_seconds()

# number of times to repeat each operation (initial)
initial_repeats = 4

# number of times to repeat each operation (max)
max_repeats = 1024

dashes = "".join(("-" for _ in range(0, 30)))


def new_telemetry_message():
    return {"payload": next_random_string("telemetry")}


def pretty_time(t):
    """
    return pretty string for datetime and timedelta objects (no date, second accuracy)
    """
    if isinstance(t, datetime.timedelta):
        return str(datetime.timedelta(seconds=t.seconds))
    else:
        return t.strftime("%H:%M:%S")


class TimeLimit(object):
    def __init__(self, test_run_time):
        self.test_run_time = test_run_time
        self.test_start_time = datetime.datetime.now()
        self.test_end_time = self.test_start_time + self.test_run_time

    def is_test_done(self):
        return datetime.datetime.now() >= self.test_end_time

    def print_progress(self, logger):
        now = datetime.datetime.now()
        logger("Start time: {}".format(pretty_time(self.test_start_time)))
        logger("Duration:   {}".format(pretty_time(self.test_run_time)))
        logger("End time:   {}".format(pretty_time(self.test_end_time)))
        logger("now:        {}".format(pretty_time(now)))
        logger("Time left:  {}".format(pretty_time(self.test_end_time - now)))


@pytest.mark.testgroup_stress
@pytest.mark.describe("EdgeHub Module Client Stress")
@pytest.mark.timeout(test_timeout)
class TestStressEdgeHubModuleClient(object):
    @pytest.fixture
    def client(self, test_module):
        return test_module

    @pytest.mark.it("Run for {}".format(pretty_time(test_run_time)))
    async def test_stress(
        self,
        logger,
        client,
        eventhub,
        service,
        registry,
        friend,
        leaf_device,
        sample_desired_props,
        sample_reported_props,
    ):

        time_limit = TimeLimit(test_run_time)

        count = initial_repeats

        while count <= max_repeats:
            if time_limit.is_test_done():
                return

            logger(dashes)
            logger("Next Iteration. Running with {} operations per step".format(count))
            time_limit.print_progress(logger)
            logger(dashes)

            await self.do_test_telemetry(
                client=client, logger=logger, eventhub=eventhub, count=count
            )

            if time_limit.is_test_done():
                return

            await self.do_test_handle_method_from_service(
                client=client, logger=logger, service=service, count=count
            )

            if time_limit.is_test_done():
                return

            """
            await self.do_test_handle_method_to_friend(
                client=client, logger=logger, friend=friend, count=count
            )

            if time_limit.is_test_done():
                return

            await self.do_test_handle_method_to_leaf_device(
                client=client, logger=logger, leaf_device=leaf_device, count=count
            )

            if time_limit.is_test_done():
                return
            """

            await self.do_test_desired_property_patch(
                client=client,
                logger=logger,
                registry=registry,
                sample_desired_props=sample_desired_props,
                count=count,
            )

            if time_limit.is_test_done():
                return

            await self.do_test_get_twin(
                client=client,
                logger=logger,
                registry=registry,
                sample_desired_props=sample_desired_props,
                count=count,
            )

            if time_limit.is_test_done():
                return

            await self.do_test_reported_properties(
                client=client,
                logger=logger,
                registry=registry,
                sample_reported_props=sample_reported_props,
                count=count,
            )

            count = count * 2

            if count >= max_repeats:
                count = initial_repeats

    async def do_test_telemetry(self, *, client, logger, eventhub, count):
        logger("testing telemetry with {} operations".format(count))

        payloads = [new_telemetry_message() for x in range(0, count)]
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

            if len(payloads):
                received_message_future = asyncio.ensure_future(
                    eventhub.wait_for_next_event(client.device_id)
                )

        eventhub.disconnect_sync()

    async def do_test_get_twin(
        self, *, client, logger, registry, sample_desired_props, count
    ):
        await client.enable_twin()

        for i in range(0, count):
            logger("get_twin {}/{}".format(i + 1, count))
            twin_sent = sample_desired_props()

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

    async def patch_desired(
        self, *, client, registry, logger, sample_desired_props, mistakes=1
    ):
        twin_sent = sample_desired_props()
        logger("Patching desired properties to {}".format(twin_sent))

        patch_future = asyncio.ensure_future(
            wait_for_desired_properties_patch(
                client=client, expected_twin=twin_sent, logger=logger, mistakes=mistakes
            )
        )
        await asyncio.sleep(1)  # wait for async call to take effect

        await patch_desired_props(registry, client, twin_sent)

        await patch_future  # raises if patch not received

    async def do_test_desired_property_patch(
        self, *, client, logger, registry, sample_desired_props, count
    ):
        await client.enable_twin()

        # flush the desired property queue.  This is mostly removing
        # patches from previous get_twin tests, so we set mistakes to a large
        # number
        await self.patch_desired(
            client=client,
            registry=registry,
            logger=logger,
            sample_desired_props=sample_desired_props,
            mistakes=max_repeats * 2,
        )

        for i in range(0, count):
            logger("desired_property_patch {}/{}".format(i + 1, count))
            await self.patch_desired(
                client=client,
                registry=registry,
                logger=logger,
                sample_desired_props=sample_desired_props,
            )
            logger("patch {} received".format(i))

    async def do_test_reported_properties(
        self, *, client, logger, registry, sample_reported_props, count
    ):
        await client.enable_twin()

        for i in range(0, count):
            logger("reported_properties {}/{}".format(i + 1, count))

            properties_sent = sample_reported_props()

            await client.patch_twin(properties_sent)

            await wait_for_reported_properties_update(
                properties_sent=properties_sent,
                client=client,
                registry=registry,
                logger=logger,
            )

    async def do_test_handle_method_from_service(
        self, *, client, logger, service, count
    ):

        for i in range(0, count):
            logger("method_from_service {}/{}".format(i + 1, count))

            # BKTODO: pull enable_methods out of run_method_call_test

            await run_method_call_test(
                source=service, destination=client, logger=logger
            )

    async def do_test_handle_method_to_friend(self, *, client, logger, friend, count):

        for i in range(0, count):
            logger("method_to_friend {}/{}".format(i + 1, count))

            await run_method_call_test(source=client, destination=friend, logger=logger)

    async def do_test_handle_method_to_leaf_device(
        self, *, client, logger, leaf_device, count
    ):

        for i in range(0, count):
            logger("method_to_leaf_device {}/{}".format(i + 1, count))

            # BKTODO: pull enable_methods out of run_method_call_test

            await run_method_call_test(
                source=client, destination=leaf_device, logger=logger
            )
