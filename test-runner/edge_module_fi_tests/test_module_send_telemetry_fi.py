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
def test_module_send_event_iothub_fi():
    try:
        log_message("connecting module client")
        module_client = connections.connect_test_module_client()
        log_message("connecting eventhub client")
        eventhub_client = connections.connect_eventhub_client()
        sent_message = test_utilities.random_string_in_json()
        disconnect_edgehub()  # DISCONNECT EDGEHUB
        log_message("sending event " + " async: " + str(sent_message))
        thread = module_client.send_event_async(sent_message)
        connect_edgehub()  # RECONNECT EDGEHUB
        log_message("getting result with timeout: " + str(local_timeout))
        thread.wait(local_timeout)  # Result is None if successful
        log_message("wait for event to arrive at eventhub")
        received_message = eventhub_client.wait_for_next_event(
            get_current_config().test_module.device_id,
            test_utilities.default_eventhub_timeout,
            expected=sent_message,
        )
        if not received_message:
            log_message("Message not received")
            assert False
        log_message("disconnecting module client")
        module_client.disconnect()
        log_message("disconnecting eventhub client")
        eventhub_client.disconnect()
    finally:
        restart_edgehub(hard=False)
