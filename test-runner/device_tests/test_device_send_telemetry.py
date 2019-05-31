#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import test_utilities
from runtime_config import get_current_config
from adapters import print_message as log_message


@pytest.mark.testgroup_iothub_device_client
@pytest.mark.timeout(timeout=180) # extra timeout in case eventhub needs to retry due to resource error
def test_device_send_event_to_iothub():

    device_client = connections.connect_test_device_client()
    eventhub_client = connections.connect_eventhub_client()

    sent_message = test_utilities.random_string_in_json()
    log_message("sending event: " + str(sent_message))
    device_client.send_event(sent_message)

    received_message = eventhub_client.wait_for_next_event(
        get_current_config().test_device.device_id,
        test_utilities.default_eventhub_timeout,
        expected=sent_message,
    )
    if not received_message:
        log_message("Message not received")
        assert False

    device_client.disconnect()
    eventhub_client.disconnect()
