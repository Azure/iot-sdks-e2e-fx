#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
import time
import wrapper_api
import environment
import json
from wrapper_api import print_message as log_message

# Amount of time to wait after updating desired properties.
wait_time_for_desired_property_updates = 5


@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.supportsTwin
def test_service_can_set_desired_properties_and_module_can_retrieve_them():

    twin_sent = {"properties": {"desired": {"foo": random.randint(1, 9999)}}}

    log_message("connecting registry client")
    registry_client = connections.connect_registry_client()
    log_message("patching twin")
    registry_client.patch_module_twin(
        environment.edge_device_id, environment.module_id, twin_sent
    )
    log_message("disconnecting registry client")
    registry_client.disconnect()

    log_message("connecting module client")
    module_client = connections.connect_test_module_client()
    log_message("enabling twin")
    module_client.enable_twin()

    log_message("getting module twin")
    twin_received = module_client.get_twin()
    log_message("disconnecting module client")
    module_client.disconnect()
    log_message("module client disconnected")

    log_message("twin sent:    " + str(twin_sent))
    log_message("twin received:" + str(twin_received))
    assert (
        twin_sent["properties"]["desired"]["foo"]
        == twin_received["properties"]["desired"]["foo"]
    )


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.supportsTwin
@pytest.mark.skipif(environment.language == "java", reason="java tests after this test are failing.  I suspect the wrapper isn't cleaning itself up correctly")
def test_service_can_set_multiple_desired_property_patches_and_module_can_retrieve_them_as_events():

    log_message("connecting registry client")
    registry_client = connections.connect_registry_client()
    log_message("connecting module client")
    module_client = connections.connect_test_module_client()
    log_message("enabling twin")
    module_client.enable_twin()

    base = random.randint(1, 9999) * 100
    for i in range(1, 4):
        log_message("start waiting for patch #" + str(i))
        patch_thread = module_client.wait_for_desired_property_patch_async()

        log_message("sending patch #" + str(i) + " through registry client")
        twin_sent = {"properties": {"desired": {"foo": base + i}}}
        registry_client.patch_module_twin(
            environment.edge_device_id, environment.module_id, twin_sent
        )
        log_message("patch " + str(i) + " sent")

        log_message("waiting for patch " + str(i) + " to arrive at module client")
        patch_received = patch_thread.get()
        log_message("patch received:" + json.dumps(patch_received))

        log_message(
            "desired properties sent:     "
            + str(twin_sent["properties"]["desired"]["foo"])
        )

        # Most of the time, the C wrapper returns a patch with "foo" at the root.  Sometimes it
        # returns a patch with "properties/desired" at the root.  I know that this has to do with timing and
        # the difference between the code that handles the initial GET and the code that handles
        # the PATCH that arrives later.  I suspect it has something to do with the handling for
        # DEVICE_TWIN_UPDATE_COMPLETE and maybe we occasionally get a full twin when we're waiting
        # for a patch, but that's just an educated guess.
        #
        # I don't know if this is happening in the SDK or in the glue.
        # this happens relatively rarely.  Maybe 1/20, maybe 1/100 times

        if "properties" in patch_received:
            log_message("desired properties received: " + str(patch_received["properties"]["desired"]["foo"]))
            assert (
                twin_sent["properties"]["desired"]["foo"]
                == patch_received["properties"]["desired"]["foo"]
            )
        else:
            log_message("desired properties recieved: " + str(patch_received["foo"]))
            assert twin_sent["properties"]["desired"]["foo"] == patch_received["foo"]

    registry_client.disconnect()
    module_client.disconnect()
