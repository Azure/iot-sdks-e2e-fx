# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import test_utilities
import json
from runtime_config import get_current_config
from adapters import print_message as log_message
from models import HubEvent


# extra timeout in case eventhub needs to retry due to resource error
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.timeout(timeout=180)
def test_device_send_event_to_iothub(test_object_stringified):

    try:
        device_client = connections.connect_test_device_client()
        eventhub_client = connections.connect_eventhub_client()

        device_client.send_event(test_object_stringified)

        received_message = eventhub_client.wait_for_next_event(
            get_current_config().test_device.device_id,
            test_utilities.default_eventhub_timeout,
            expected=test_object_stringified,
        )
        if not received_message:
            log_message("Message not received")
            assert False

    finally:
        device_client.disconnect()
        eventhub_client.disconnect()


# extra timeout in case eventhub needs to retry due to resource error
@pytest.mark.uses_new_message_format
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.timeout(timeout=180)
def test_device_send_string_using_new_message_format(test_string):
    try:
        device_client = connections.connect_test_device_client()
        eventhub_client = connections.connect_eventhub_client()

        sent_message = HubEvent()
        sent_message.body = json.dumps(test_string)

        device_client.send_event(sent_message.convert_to_json())

        received_message = eventhub_client.wait_for_next_event(
            get_current_config().test_device.device_id,
            test_utilities.default_eventhub_timeout,
            expected=sent_message.body,
        )
        if not received_message:
            log_message("Message not received")
            assert False

    finally:
        device_client.disconnect()
        eventhub_client.disconnect()
