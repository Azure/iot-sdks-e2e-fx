#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import time
import test_utilities
import wrapper_api
from wrapper_api import print_message as log_message
from edgehub_control import (
    disconnect_edgehub,
    connect_edgehub,
    edgeHub,
    restart_edgehub,
)

output_name = "loopout"
input_name = "loopin"
receive_timeout = 60

"""
Module sending message to itself
Loopout and Loopin are linked together on the deployment manifest
"""

@pytest.mark.skip
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.callsendOutputMessage
@pytest.mark.receivesInputMessages
@pytest.mark.handlesLoopbackMessages
def test_module_input_output_loopback_fi():
    log_message("connecting module client")
    module_client = connections.connect_test_module_client()
    log_message("enabling input messages")
    module_client.enable_input_messages()

    log_message("listening for input messages")
    input_thread = module_client.wait_for_input_event_async(input_name)

    sent_message = test_utilities.max_random_string()

    disconnect_edgehub()  # Disconnect Edgehub
    module_client.send_output_event(output_name, sent_message)
    connect_edgehub()  # Reconnect Edgehub
    log_message("sent output event: " + str(sent_message))
    log_message("waiting for input message to arrive")
    received_message = input_thread.get(receive_timeout)
    log_message("input message arrived")
    log_message("expected message: " + str(sent_message))
    log_message("received message: " + str(received_message))
    assert received_message == sent_message
    module_client.disconnect()

