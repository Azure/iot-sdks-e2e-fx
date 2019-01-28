#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random

import pytest

import connections
import environment
import test_utilities
from edgehub_control import (
    connect_edgehub,
    disconnect_edgehub,
    edgeHub,
    restart_edgehub,
)
from adapters import print_message as log_message

local_timeout = 60  # Seconds

# TODO: Make sure that testing environment is same linux environment that modules are running on.


@pytest.mark.skip
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.callsSendEvent
def test_module_send_multiple_event_iothub_fi():
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

        log_message("disconnecting edgehub")
        disconnect_edgehub()  # DISCONNECT EDGEHUB
        print("PYTEST FAKE: begin sending events async...")
        # Send String of Messages Asynchronously to create a queue
        for i in range(5):
            print(
                "PYTEST FAKE: sending event " + str(i) + " async: " + str(sent_message)
            )
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
