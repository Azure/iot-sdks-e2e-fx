#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
from runtime_config import get_current_config
from adapters import print_message as log_message


@pytest.mark.timeout(180)
@pytest.mark.supportsTwin
@pytest.mark.testgroup_iothub_device_client
def test_device_can_set_reported_properties_and_service_can_retrieve_them():
    reported_properties_sent = {"foo": random.randint(1, 9999)}

    device_client = connections.connect_test_device_client()
    device_client.enable_twin()
    device_client.patch_twin(reported_properties_sent)
    device_client.disconnect()

    registry_client = connections.connect_registry_client()
    twin_received = registry_client.get_device_twin(
        get_current_config().test_device.device_id
    )
    registry_client.disconnect()

    reported_properties_received = twin_received["properties"]["reported"]
    if "$version" in reported_properties_received:
        del reported_properties_received["$version"]
    if "$metadata" in reported_properties_received:
        del reported_properties_received["$metadata"]
    log_message("expected:" + str(reported_properties_sent))
    log_message("received:" + str(reported_properties_received))

    assert reported_properties_sent == reported_properties_received
