#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
import time
from runtime_config import get_current_config
import json
from adapters import print_message as log_message

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
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.supportsTwin
def test_service_can_set_desired_properties_and_device_can_retrieve_them():

    twin_sent = {"properties": {"desired": {"foo": random.randint(1, 9999)}}}

    registry_client = connections.connect_registry_client()
    registry_client.patch_device_twin(
        get_current_config().test_device.device_id, twin_sent
    )
    registry_client.disconnect()

    device_client = connections.connect_test_device_client()
    device_client.enable_twin()

    twin_received = device_client.get_twin()
    device_client.disconnect()

    log_message("twin sent:    " + str(twin_sent))
    log_message("twin received:" + str(twin_received))
    assert (
        twin_sent["properties"]["desired"]["foo"]
        == twin_received["properties"]["desired"]["foo"]
    )


@pytest.mark.testgroup_iothub_device_client
@pytest.mark.supportsTwin
def test_service_can_set_multiple_desired_property_patches_and_device_can_retrieve_them_as_events():

    registry_client = connections.connect_registry_client()
    device_client = connections.connect_test_device_client()
    device_client.enable_twin()

    base = random.randint(1, 9999) * 100
    for i in range(1, 4):
        twin_sent = {"properties": {"desired": {"foo": base + i}}}
        registry_client.patch_device_twin(
            get_current_config().test_device.device_id, twin_sent
        )

        patch_thread = device_client.wait_for_desired_property_patch_async()

        twin_sent = {"properties": {"desired": {"foo": base + i}}}
        registry_client.patch_device_twin(
            get_current_config().test_device.device_id, twin_sent
        )

        done = False
        mistakes_left = 1
        while not done:
            log_message("getting patch " + str(i) + " on device client")
            patch_received = patch_thread.get()
            log_message("patch received:" + json.dumps(patch_received))

            log_message(
                "desired properties sent:     "
                + str(twin_sent["properties"]["desired"]["foo"])
            )

            foo_val = get_patch_received(patch_received)
            if foo_val == -1:
                log_message("patch received of invalid format!")
                assert 0
            log_message("desired properties recieved: " + str(foo_val))

            if twin_sent["properties"]["desired"]["foo"] == foo_val:
                log_message("success")
                done = True
            else:
                if mistakes_left:
                    # We sometimes get the old value before we get the new value, and that's
                    # perfectly valid (especially with QOS 1 on MQTT).  If we got the wrong
                    # value, we just try again.
                    mistakes_left = mistakes_left - 1
                    log_message(
                        "trying again.  We still have {} mistakes left".format(
                            mistakes_left
                        )
                    )
                    log_message("start waiting for patch #{} again".format(i))
                    patch_thread = device_client.wait_for_desired_property_patch_async()
                else:
                    log_message("too many mistakes.  Failing")
                    assert False

    registry_client.disconnect()
    device_client.disconnect()
