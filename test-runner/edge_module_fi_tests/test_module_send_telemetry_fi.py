# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
from runtime_config import get_current_config
from adapters import print_message
from edgehub_control import (
    edgeHub,
    disconnect_edgehub,
    connect_edgehub,
    restart_edgehub,
)


local_timeout = 60  # Seconds


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.callsSendEvent
@pytest.mark.timeout(
    timeout=180
)  # extra timeout in case eventhub needs to retry due to resource error
def test_module_send_event_iothub_fi(
    test_object_stringified, test_object_stringified_2
):
    """ Sends event through Edge Hub to IoT Hub and validates the message is received using the Event Hub API.

    The module client is in the langauge being tested, and the eventhub client is directly connected to Azure to receive the event.
    """
    module_client = connections.connect_test_module_client()
    eventhub_client = connections.connect_eventhub_client()
    module_client.send_event_async(test_object_stringified)
    received_message = eventhub_client.wait_for_next_event(
        get_current_config().test_module.device_id, expected=test_object_stringified
    )
    if not received_message:
        print_message("Intial message not received")
        assert False
    disconnect_edgehub()  # DISCONNECT EDGEHUB
    module_client.send_event_async(test_object_stringified_2)
    connect_edgehub()  # RECONNECT EDGEHUB
    received_message = eventhub_client.wait_for_next_event(
        get_current_config().test_module.device_id, expected=test_object_stringified_2
    )
    if not received_message:
        print_message("Second message not received")
        assert False
    module_client.disconnect()
    eventhub_client.disconnect()
