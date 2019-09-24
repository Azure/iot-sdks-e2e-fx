# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
from runtime_config import get_current_config
from edgehub_control import (
    disconnect_edgehub,
    connect_edgehub,
    edgeHub,
    restart_edgehub,
)
from adapters import print_message

output_name = "telemetry"

"""
Send Output Event
There's a rule in the routing table that sends the 'telemetry' output event to eventhub
"""


@pytest.mark.callsSendOutputEvent
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.timeout(
    timeout=180
)  # extra timeout in case eventhub needs to retry due to resource error
def test_module_output_routed_upstream_fi(test_object_stringified):
    try:
        module_client = connections.connect_test_module_client()
        eventhub_client = connections.connect_eventhub_client()

        disconnect_edgehub()
        connect_edgehub()
        module_client.send_output_event(output_name, test_object_stringified)

        received_message = eventhub_client.wait_for_next_event(
            get_current_config().test_module.device_id, expected=test_object_stringified
        )
        if not received_message:
            print_message("Message not received")
            assert False

        module_client.disconnect()
        eventhub_client.disconnect()
    finally:
        restart_edgehub(hard=False)
