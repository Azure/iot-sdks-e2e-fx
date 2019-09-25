# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
import time
import asyncio
from runtime_config import get_current_config
import json
from adapters import print_message
from edgehub_control import connect_edgehub, disconnect_edgehub, restart_edgehub
from time import sleep
import docker

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
async def test_service_can_set_desired_properties_and_module_can_retrieve_them_fi():
    twin_sent = {"properties": {"desired": {"foo": random.randint(1, 9999)}}}

    print_message("connecting registry client")
    registry_client = connections.connect_registry_client()
    print_message("disconnecting edgehub")
    sleep(2)
    disconnect_edgehub()  # DISCONNECTING EGEHUB
    connect_edgehub()  # CONNECTING EDGEHUB
    await registry_client.patch_module_twin(
        get_current_config().test_module.device_id,
        get_current_config().test_module.module_id,
        twin_sent,
    )
    print_message("patching twin")
    print_message("disconnecting registry client")
    registry_client.disconnect_sync()

    print_message("connecting module client")
    module_client = connections.connect_test_module_client()
    print_message("enabling twin")
    await module_client.enable_twin()
    print_message("disconnecting edgehub")
    sleep(2)
    disconnect_edgehub()  # DISCONNECTING EGEHUB
    sleep(5)
    connect_edgehub()  # CONNECTING EDGEHUB
    twin_received = await module_client.get_twin()
    print_message("getting module twin")
    print_message("disconnecting module client")
    module_client.disconnect_sync()
    print_message("module client disconnected")
    print_message("twin sent:    " + str(twin_sent))
    print_message("twin received:" + str(twin_received))
    assert (
        twin_sent["properties"]["desired"]["foo"]
        == twin_received["properties"]["desired"]["foo"]
    )


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.supportsTwin
async def test_service_can_set_multiple_desired_property_patches_and_module_can_retrieve_them_as_events_fi():

    print_message("connecting registry client")
    registry_client = connections.connect_registry_client()
    print_message("connecting module client")
    module_client = connections.connect_test_module_client()
    print_message("enabling twin")
    await module_client.enable_twin()

    base = random.randint(1, 9999) * 100
    for i in range(1, 4):
        print_message(
            "sending patch #" + str(i) + " through registry client"
        )  # Send patch
        twin_sent = {"properties": {"desired": {"foo": base + i}}}
        await registry_client.patch_module_twin(
            get_current_config().test_module.device_id,
            get_current_config().test_module.module_id,
            twin_sent,
        )
        print_message("patch " + str(i) + " sent")
        print_message("start waiting for patch #" + str(i))
        patch_future = asyncio.ensure_future(
            module_client.wait_for_desired_property_patch()
        )  # Set Twin Callback
        print_message("Fault Injection: disconnecting edgehub")
        disconnect_edgehub()  # DISCONNECTING EGEHUB
        print_message("Fault Injection: reconnecting edgehub")
        connect_edgehub()  # CONNECTING EDGEHUB
        sleep(2)
        print_message(
            "Tringgering patch #" + str(i) + " through registry client"
        )  # Trigger Twin Callback
        await registry_client.patch_module_twin(
            get_current_config().test_module.device_id,
            get_current_config().test_module.module_id,
            twin_sent,
        )
        print_message("patch " + str(i) + " triggered")
        print_message("waiting for patch " + str(i) + " to arrive at module client")
        patch_received = await patch_future  # Get twin from patch received
        print_message("patch received:" + json.dumps(patch_received))
        print_message(
            "desired properties sent:     "
            + str(twin_sent["properties"]["desired"]["foo"])
        )
        foo_val = get_patch_received(patch_received)
        if foo_val == -1:
            print_message("patch received of invalid format!")
            assert 0
        print_message("desired properties recieved: " + str(foo_val))
        assert twin_sent["properties"]["desired"]["foo"] == foo_val

    registry_client.disconnect_sync()
    module_client.disconnect_sync()
