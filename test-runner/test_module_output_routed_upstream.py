#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import test_utilities
import environment

output_name = "telemetry"


@pytest.mark.callsSendOutputEvent
@pytest.mark.testgroup_edgehub_module_client
def test_module_output_routed_upstream():

    module_client = connections.connect_test_module_client()
    eventhub_client = connections.connect_eventhub_client()
    eventhub_client.enable_telemetry()

    input_thread = eventhub_client.wait_for_event_async(environment.edge_device_id)

    sent_message = test_utilities.random_string_in_json()
    module_client.send_output_event(output_name, sent_message)

    received_message = input_thread.get(test_utilities.default_eventhub_timeout)
    test_utilities.assert_json_equality(received_message, sent_message)

    module_client.disconnect()
    eventhub_client.disconnect()
