#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import test_utilities
from environment import runtime_config
from edgehub_control import (
    disconnect_edgehub,
    connect_edgehub,
    edgeHub,
    restart_edgehub,
)
from adapters import print_message as log_message

output_name = "telemetry"

"""
Send Output Event
There's a rule in the routing table that sends the 'telemetry' output event to eventhub
"""


@pytest.mark.callsSendOutputEvent
@pytest.mark.testgroup_edgehub_fault_injection
def test_module_output_routed_upstream_fi():
    try:
        module_client = connections.connect_test_module_client()
        eventhub_client = connections.connect_eventhub_client()

        disconnect_edgehub()
        connect_edgehub()
        sent_message = test_utilities.random_string_in_json()
        module_client.send_output_event(output_name, sent_message)

        received_message = eventhub_client.wait_for_next_event(
            runtime_config.test_module.device_id,
            test_utilities.default_eventhub_timeout,
            expected=sent_message,
        )
        if not received_message:
            log_message("Message not received")
            assert False

        module_client.disconnect()
        eventhub_client.disconnect()
    finally:
        restart_edgehub(hard=False)
