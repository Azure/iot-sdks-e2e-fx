# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import json
import asyncio

# Amount of time to wait after updating desired properties.
wait_time_for_desired_property_updates = 5


def get_patch_received(patch_received):
    """
    Helper function to take in recieved patch and extract the value of foo without returning error.
    If the patch_received is not of the correct format foo_val will be set as a blank string and returned.
    """
    if "properties" in patch_received:
        foo_val = patch_received["properties"]["desired"]["foo"]
    elif "desired" in patch_received:
        foo_val = patch_received["desired"]["foo"]
    elif "foo" in patch_received:
        foo_val = patch_received["foo"]
    else:
        foo_val = -1
    return foo_val


async def patch_desired_props(registry, client, props):
    if getattr(client, "module_id", None):
        await registry.patch_module_twin(client.device_id, client.module_id, props)
    else:
        await registry.patch_device_twin(client.device_id, props)


async def wait_for_reported_properties_update(
    *, reported_properties_sent, client, registry, logger
):
    """
    Helper function which uses the registry to wait for reported properties
    to update to the expected value
    """
    while True:
        if getattr(client, "module_id", None):
            twin_received = await registry.get_module_twin(
                client.device_id, client.module_id
            )
        else:
            twin_received = await registry.get_device_twin(client.device_id)

        reported_properties_received = twin_received["properties"]["reported"]
        if "$version" in reported_properties_received:
            del reported_properties_received["$version"]
        if "$metadata" in reported_properties_received:
            del reported_properties_received["$metadata"]
        logger("expected:" + str(reported_properties_sent))
        logger("received:" + str(reported_properties_received))

        if reported_properties_sent == reported_properties_received:
            # test passed
            return
        else:
            logger("Twin does not match.  Sleeping for 5 seconds and retrying.")
            await asyncio.sleep(5)


async def wait_for_desired_properties_patch(*, client, expected_twin, logger):
    mistakes_left = 1
    while True:
        patch_received = await client.wait_for_desired_property_patch()
        logger(
            "desired properties sent:     "
            + str(expected_twin["properties"]["desired"]["foo"])
        )

        foo_val = get_patch_received(patch_received)
        if foo_val == -1:
            logger("patch received of invalid format!")
            assert 0
        logger("desired properties recieved: " + str(foo_val))

        if expected_twin["properties"]["desired"]["foo"] == foo_val:
            logger("success")
            return
        else:
            if mistakes_left:
                # We sometimes get the old value before we get the new value, and that's
                # perfectly valid (especially with QOS 1 on MQTT).  If we got the wrong
                # value, we just try again.
                mistakes_left = mistakes_left - 1
                logger(
                    "trying again.  We still have {} mistakes left".format(
                        mistakes_left
                    )
                )
            else:
                logger("too many mistakes.  Failing")
                assert False


class TwinTests(object):
    @pytest.mark.it("Can connect, enable twin, and disconnect")
    async def test_client_connect_enable_twin_disconnect(self, client):
        await client.enable_twin()

    @pytest.mark.timeout(180)
    @pytest.mark.supportsTwin
    @pytest.mark.it("Can get the most recent twin from the service")
    async def test_twin_desired_props(
        self, client, logger, registry, sample_desired_props
    ):
        twin_sent = sample_desired_props()

        await patch_desired_props(registry, client, twin_sent)

        # BKTODO: Node needs this sleep to pass MQTT against edgeHub
        await asyncio.sleep(5)
        await client.enable_twin()

        while True:
            twin_received = await client.get_twin()

            logger("twin sent:    " + str(twin_sent))
            logger("twin received:" + str(twin_received))
            if (
                twin_sent["properties"]["desired"]["foo"]
                == twin_received["properties"]["desired"]["foo"]
            ):
                # test passed
                return
            else:
                logger("Twin does not match.  Sleeping for 5 seconds and retrying.")
                await asyncio.sleep(5)

    @pytest.mark.timeout(180)
    @pytest.mark.supportsTwin
    @pytest.mark.it("Can get the most recent twin from the service 5 times")
    @pytest.mark.skip("Failing on pythonv2")
    async def test_twin_desired_props_5_times(
        self, client, logger, registry, sample_desired_props
    ):
        await client.enable_twin()

        for _ in range(0, 5):
            twin_sent = sample_desired_props()

            await patch_desired_props(registry, client, twin_sent)

            while True:
                twin_received = await client.get_twin()

                logger("twin sent:    " + str(twin_sent))
                logger("twin received:" + str(twin_received))
                if (
                    twin_sent["properties"]["desired"]["foo"]
                    == twin_received["properties"]["desired"]["foo"]
                ):
                    break
                else:
                    logger("Twin does not match.  Sleeping for 5 seconds and retrying.")
                    await asyncio.sleep(5)

    @pytest.mark.supportsTwin
    @pytest.mark.it("Can receive desired property patches as events")
    async def test_twin_desired_props_patch(
        self, client, logger, registry, sample_desired_props
    ):

        await client.enable_twin()

        for i in range(1, 4):
            twin_sent = sample_desired_props()

            logger("start waiting for patch {}".format(i))
            patch_future = asyncio.ensure_future(
                wait_for_desired_properties_patch(
                    client=client, expected_twin=twin_sent, logger=logger
                )
            )
            await asyncio.sleep(3)  # wait for async call to take effect

            await patch_desired_props(registry, client, twin_sent)
            logger("patch {} sent".format(i))

            await patch_future  # raises if patch not received
            logger("patch {} received".format(i))

    @pytest.mark.timeout(180)
    @pytest.mark.supportsTwin
    @pytest.mark.it(
        "Can set reported properties which can be successfully retrieved by the service"
    )
    async def test_twin_reported_props(
        self, client, logger, registry, sample_reported_props
    ):
        reported_properties_sent = sample_reported_props()

        await client.enable_twin()
        await client.patch_twin(reported_properties_sent)

        await wait_for_reported_properties_update(
            reported_properties_sent=reported_properties_sent,
            client=client,
            registry=registry,
            logger=logger,
        )

    @pytest.mark.timeout(180)
    @pytest.mark.supportsTwin
    @pytest.mark.it(
        "Can set reported properties 5 times and retrieve them from the service"
    )
    async def test_twin_reported_props_5_times(
        self, client, logger, registry, sample_reported_props
    ):
        await client.enable_twin()

        for _ in range(0, 5):
            reported_properties_sent = sample_reported_props()

            await client.patch_twin(reported_properties_sent)

            await wait_for_reported_properties_update(
                reported_properties_sent=reported_properties_sent,
                client=client,
                registry=registry,
                logger=logger,
            )
