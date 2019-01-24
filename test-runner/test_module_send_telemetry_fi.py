#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import test_utilities
import wrapper_api
import environment
from wrapper_api import print_message as log_message
from edgehub_control import (
    edgeHub,
    disconnect_edgehub,
    connect_edgehub,
    restart_edgehub,
)


local_timeout = 60  # Seconds


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.callsSendEvent
def test_module_send_event_iothub_fi():
    try:
        log_message("connecting module client")
        module_client = connections.connect_test_module_client()
        log_message("connecting eventhub client")
        eventhub_client = connections.connect_eventhub_client()
        log_message("enabling telemetry on eventhub client")
        eventhub_client.enable_telemetry()
        log_message("start waiting for events on eventhub")
        input_thread = eventhub_client.wait_for_event_async(environment.edge_device_id)
        sent_message = test_utilities.random_string_in_json()
        disconnect_edgehub()  # DISCONNECT EDGEHUB
        log_message("sending event " + " async: " + str(sent_message))
        thread = module_client.send_event_async(sent_message)
        connect_edgehub()  # RECONNECT EDGEHUB
        log_message("getting result with timeout: " + str(local_timeout))
        thread.wait(local_timeout)  # Result is None if successful
        log_message("wait for event to arrive at eventhub")
        received_message = input_thread.get(test_utilities.default_eventhub_timeout)
        log_message("expected event: " + str(sent_message))
        log_message("received event: " + str(received_message))
        test_utilities.assert_json_equality(received_message, sent_message)
        log_message("disconnecting module client")
        module_client.disconnect()
        log_message("disconnecting eventhub client")
        eventhub_client.disconnect()
    finally:
        restart_edgehub(hard=False)

