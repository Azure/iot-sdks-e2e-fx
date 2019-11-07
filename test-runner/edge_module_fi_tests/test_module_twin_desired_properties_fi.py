# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
import time
import asyncio
import json
from horton_settings import settings
from edgehub_control import connect_edgehub, disconnect_edgehub, restart_edgehub
from time import sleep
import docker

pytestmark = pytest.mark.asyncio

client = docker.from_env()

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


@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.supportsTwin
async def test_service_can_set_desired_properties_and_module_can_retrieve_them_fi(
    logger
):
    twin_sent = {"properties": {"desired": {"foo": random.randint(1, 9999)}}}

    logger("connecting registry client")
    registry_client = connections.connect_registry_client()
    logger("disconnecting edgehub")
    sleep(2)
    disconnect_edgehub()  # DISCONNECTING EGEHUB
    connect_edgehub()  # CONNECTING EDGEHUB
    await registry_client.patch_module_twin(
        settings.test_module.device_id, settings.test_module.module_id, twin_sent
    )
    logger("patching twin")
    logger("disconnecting registry client")
    registry_client.disconnect_sync()

    logger("connecting module client")
    module_client = connections.connect_test_module_client()
    logger("enabling twin")
    await module_client.enable_twin()
    logger("disconnecting edgehub")
    sleep(2)
    disconnect_edgehub()  # DISCONNECTING EGEHUB
    sleep(5)
    connect_edgehub()  # CONNECTING EDGEHUB
    twin_received = await module_client.get_twin()
    logger("getting module twin")
    logger("disconnecting module client")
    module_client.disconnect_sync()
    logger("module client disconnected")
    logger("twin sent:    " + str(twin_sent))
    logger("twin received:" + str(twin_received))
    assert (
        twin_sent["properties"]["desired"]["foo"]
        == twin_received["properties"]["desired"]["foo"]
    )


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.supportsTwin
async def test_service_can_set_multiple_desired_property_patches_and_module_can_retrieve_them_as_events_fi(
    logger
):

    logger("connecting registry client")
    registry_client = connections.connect_registry_client()
    logger("connecting module client")
    module_client = connections.connect_test_module_client()
    logger("enabling twin")
    await module_client.enable_twin()

    base = random.randint(1, 9999) * 100
    for i in range(1, 4):
        logger("sending patch #" + str(i) + " through registry client")  # Send patch
        twin_sent = {"properties": {"desired": {"foo": base + i}}}
        await registry_client.patch_module_twin(
            settings.test_module.device_id, settings.test_module.module_id, twin_sent
        )
        logger("patch " + str(i) + " sent")
        logger("start waiting for patch #" + str(i))
        patch_future = asyncio.ensure_future(
            module_client.wait_for_desired_property_patch()
        )  # Set Twin Callback
        logger("Fault Injection: disconnecting edgehub")
        disconnect_edgehub()  # DISCONNECTING EGEHUB
        logger("Fault Injection: reconnecting edgehub")
        connect_edgehub()  # CONNECTING EDGEHUB
        sleep(2)
        logger(
            "Tringgering patch #" + str(i) + " through registry client"
        )  # Trigger Twin Callback
        await registry_client.patch_module_twin(
            settings.test_module.device_id, settings.test_module.module_id, twin_sent
        )
        logger("patch " + str(i) + " triggered")
        logger("waiting for patch " + str(i) + " to arrive at module client")
        patch_received = await patch_future  # Get twin from patch received
        logger("patch received:" + json.dumps(patch_received))
        logger(
            "desired properties sent:     "
            + str(twin_sent["properties"]["desired"]["foo"])
        )
        foo_val = get_patch_received(patch_received)
        if foo_val == -1:
            logger("patch received of invalid format!")
            assert 0
        logger("desired properties recieved: " + str(foo_val))
        assert twin_sent["properties"]["desired"]["foo"] == foo_val

    registry_client.disconnect_sync()
    module_client.disconnect_sync()
