# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import json
import asyncio

# Amount of time to wait after updating desired properties.
wait_time_for_desired_property_updates = 5


async def patch_desired_props(registry, client, twin):
    if getattr(client, "module_id", None):
        await registry.patch_module_twin(client.device_id, client.module_id, twin)
    else:
        await registry.patch_device_twin(client.device_id, twin)


async def wait_for_reported_properties_update(
    *, properties_sent, client, registry, logger
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

        reported_properties_received = twin_received["reported"]
        if "$version" in reported_properties_received:
            del reported_properties_received["$version"]
        if "$metadata" in reported_properties_received:
            del reported_properties_received["$metadata"]
        logger("expected:" + str(properties_sent["reported"]))
        logger("received:" + str(reported_properties_received))

        if properties_sent["reported"] == reported_properties_received:
            # test passed
            return
        else:
            logger("Twin does not match.  Sleeping for 2 seconds and retrying.")
            await asyncio.sleep(2)


async def wait_for_desired_properties_patch(
    *, client, expected_twin, logger, mistakes=1
):
    mistakes_left = mistakes
    while True:
        patch_received = await client.wait_for_desired_property_patch()
        logger("desired properties sent:     " + str(expected_twin["desired"]["foo"]))

        logger("desired properties received: " + str(patch_received["desired"]["foo"]))

        if expected_twin["desired"]["foo"] == patch_received["desired"]["foo"]:
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
            if twin_sent["desired"]["foo"] == twin_received["desired"]["foo"]:
                # test passed
                return
            else:
                logger("Twin does not match.  Sleeping for 5 seconds and retrying.")
                await asyncio.sleep(5)

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
                if twin_sent["desired"]["foo"] == twin_received["desired"]["foo"]:
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

            logger("sending patch {}".format(i))
            await patch_desired_props(registry, client, twin_sent)
            logger("patch {} sent".format(i))

            await patch_future  # raises if patch not received
            logger("patch {} received".format(i))

    @pytest.mark.supportsTwin
    @pytest.mark.it(
        "Can set reported properties which can be successfully retrieved by the service"
    )
    async def test_twin_reported_props(
        self, client, logger, registry, sample_reported_props
    ):
        properties_sent = sample_reported_props()

        await client.enable_twin()
        await client.patch_twin(properties_sent)

        await wait_for_reported_properties_update(
            properties_sent=properties_sent,
            client=client,
            registry=registry,
            logger=logger,
        )

    @pytest.mark.supportsTwin
    @pytest.mark.it(
        "Can set reported properties 5 times and retrieve them from the service"
    )
    async def test_twin_reported_props_5_times(
        self, client, logger, registry, sample_reported_props
    ):
        await client.enable_twin()

        for _ in range(0, 5):
            properties_sent = sample_reported_props()

            await client.patch_twin(properties_sent)

            await wait_for_reported_properties_update(
                properties_sent=properties_sent,
                client=client,
                registry=registry,
                logger=logger,
            )
