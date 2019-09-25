# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
from runtime_config import get_current_config
from edgehub_control import connect_edgehub, disconnect_edgehub, restart_edgehub


@pytest.fixture(scope="module", autouse=True)
def set_channels(request):
    global friend_to_test_output
    global test_to_friend_input
    friend_to_test_output = "to" + get_current_config().test_module.module_id
    test_to_friend_input = "from" + get_current_config().test_module.module_id


friend_to_test_output = None
friend_to_test_input = "fromFriend"

test_to_friend_output = "toFriend"
test_to_friend_input = None

receive_timeout = 60


@pytest.mark.callsSendOutputEvent
def test_module_to_friend_routing(test_string):
    test_client = connections.connect_test_module_client()
    friend_client = connections.connect_friend_module_client()
    friend_client.enable_input_messages()

    friend_input_thread = friend_client.wait_for_input_event_async(test_to_friend_input)

    test_client.send_output_event(test_to_friend_output, test_string)

    received_message = friend_input_thread.get(receive_timeout)
    assert received_message == test_string

    friend_client.disconnect_sync()
    test_client.disconnect_sync()


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.receivesInputMessages
def test_friend_to_module_routing_fi(test_string):

    test_client = connections.connect_test_module_client()
    test_client.enable_input_messages()
    friend_client = connections.connect_friend_module_client()

    test_input_thread = test_client.wait_for_input_event_async(friend_to_test_input)

    friend_client.send_output_event(friend_to_test_output, test_string)

    received_message = test_input_thread.get(receive_timeout)
    assert received_message == test_string

    friend_client.disconnect_sync()
    test_client.disconnect_sync()
