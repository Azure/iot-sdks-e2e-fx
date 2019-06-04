#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import test_utilities
from runtime_config import get_current_config
from adapters import print_message as log_message
from edgehub_control import (
    edgeHub,
    disconnect_edgehub,
    connect_edgehub,
    restart_edgehub,
)


local_timeout = 60  # Seconds



@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.callsSendEvent
@pytest.mark.timeout(timeout=180) # extra timeout in case eventhub needs to retry due to resource error
def test_module_send_event_iothub_fi():
    """ Sends event through Edge Hub to IoT Hub and validates the message is received using the Event Hub API.

    The module client is in the langauge being tested, and the eventhub client is directly connected to Azure to receive the event.
    """
    log_message("connecting module client")
    module_client = connections.connect_test_module_client()
    log_message("connecting eventhub client")
    eventhub_client = connections.connect_eventhub_client()
    sent_message = test_utilities.random_string_in_json()
    log_message("sending event " + " async: " + str(sent_message))
    module_client.send_event_async(sent_message)
    log_message("wait for event to arrive at eventhub")
    received_message = eventhub_client.wait_for_next_event(
        get_current_config().test_module.device_id,
        test_utilities.default_eventhub_timeout,
        expected=sent_message,
    )
    if not received_message:
        log_message("Intial message not received")
        assert False
    disconnect_edgehub()  # DISCONNECT EDGEHUB
    module_client.send_event_async(sent_message)
    connect_edgehub()  # RECONNECT EDGEHUB
    received_message = eventhub_client.wait_for_next_event(
        get_current_config().test_module.device_id,
        test_utilities.default_eventhub_timeout,
        expected=sent_message,
    )
    if not received_message:
        log_message("Second message not received")
        assert False
    log_message("disconnecting module client")
    module_client.disconnect()
    log_message("disconnecting eventhub client")
    eventhub_client.disconnect()
