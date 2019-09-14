# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import json
import time

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


class TwinTests(object):
    @pytest.mark.it("Can connect, enable twin, and disconnect")
    def test_client_connect_enable_twin_disconnect(self, client):
        client.enable_twin()

    @pytest.mark.timeout(180)
    @pytest.mark.supportsTwin
    @pytest.mark.it("Can get the most recent twin from the service")
    def test_service_can_set_desired_properties_and_client_can_retrieve_them(
        self, client, logger, registry
    ):

        twin_sent = {"properties": {"desired": {"foo": random.randint(1, 9999)}}}

        if getattr(client, "module_id", None):
            registry.patch_module_twin(client.device_id, client.module_id, twin_sent)
        else:
            registry.patch_device_twin(client.device_id, twin_sent)

        logger("sleeping for an arbitrary 10 seconds so properties can propagate")
        time.sleep(10)

        # BKTODO: this test fails when the enable is at the top of the file.
        # new test case?
        client.enable_twin()
        twin_received = client.get_twin()

        logger("twin sent:    " + str(twin_sent))
        logger("twin received:" + str(twin_received))
        assert (
            twin_sent["properties"]["desired"]["foo"]
            == twin_received["properties"]["desired"]["foo"]
        )

    @pytest.mark.supportsTwin
    @pytest.mark.it("Can receive desired property patches as events")
    def test_service_can_set_multiple_desired_property_patches_and_client_can_retrieve_them_as_events(
        self, client, logger, registry
    ):

        client.enable_twin()

        base = random.randint(1, 9999) * 100
        for i in range(1, 4):
            logger("sending patch #" + str(i) + " through registry client")
            twin_sent = {"properties": {"desired": {"foo": base + i}}}

            if getattr(client, "module_id", None):
                registry.patch_module_twin(
                    client.device_id, client.module_id, twin_sent
                )
            else:
                registry.patch_device_twin(client.device_id, twin_sent)

            logger("patch " + str(i) + " sent")

            logger("start waiting for patch #" + str(i))
            patch_thread = client.wait_for_desired_property_patch_async()

            logger("Tringgering patch #" + str(i) + " through registry client")
            twin_sent = {"properties": {"desired": {"foo": base + i}}}

            if getattr(client, "module_id", None):
                registry.patch_module_twin(
                    client.device_id, client.module_id, twin_sent
                )
            else:
                registry.patch_device_twin(client.device_id, twin_sent)

            logger("patch " + str(i) + " triggered")

            done = False
            mistakes_left = 1
            while not done:
                logger("getting patch " + str(i) + " on module client")
                patch_received = patch_thread.get()
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

                if twin_sent["properties"]["desired"]["foo"] == foo_val:
                    logger("success")
                    done = True
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
                        logger("start waiting for patch #{} again".format(i))
                        patch_thread = client.wait_for_desired_property_patch_async()
                    else:
                        logger("too many mistakes.  Failing")
                        assert False

    @pytest.mark.timeout(180)
    @pytest.mark.supportsTwin
    @pytest.mark.it(
        "Can set reported properties which can be successfully retrieved by the service"
    )
    def test_module_can_set_reported_properties_and_service_can_retrieve_them(
        self, client, logger, registry
    ):
        reported_properties_sent = {"foo": random.randint(1, 9999)}

        client.enable_twin()
        client.patch_twin(reported_properties_sent)
        logger("sleeping for an arbitrary 10 seconds so properties can propagate")
        time.sleep(10)

        if getattr(client, "module_id", None):
            twin_received = registry.get_module_twin(client.device_id, client.module_id)
        else:
            twin_received = registry.get_device_twin(client.device_id)

        reported_properties_received = twin_received["properties"]["reported"]
        if "$version" in reported_properties_received:
            del reported_properties_received["$version"]
        if "$metadata" in reported_properties_received:
            del reported_properties_received["$metadata"]
        logger("expected:" + str(reported_properties_sent))
        logger("received:" + str(reported_properties_received))

        assert reported_properties_sent == reported_properties_received
