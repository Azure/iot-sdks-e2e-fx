#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import time
import test_utilities
from environment import runtime_config
from edgehub_control import connect_edgehub, disconnect_edgehub, restart_edgehub


@pytest.fixture(scope="module", autouse=True)
def set_channels(request):
    global friend_to_test_output
    global test_to_friend_input
    friend_to_test_output = "to" + runtime_config.test_module.module_id
    test_to_friend_input = "from" + runtime_config.test_module.module_id


friend_to_test_output = None
friend_to_test_input = "fromFriend"

test_to_friend_output = "toFriend"
test_to_friend_input = None

receive_timeout = 60

@pytest.mark.skip
@pytest.mark.callsSendOutputEvent
def test_module_to_friend_routing():
    test_client = connections.connect_test_module_client()
    friend_client = connections.connect_friend_module_client()
    friend_client.enable_input_messages()

    friend_input_thread = friend_client.wait_for_input_event_async(test_to_friend_input)

    sent_message = test_utilities.max_random_string()
    test_client.send_output_event(test_to_friend_output, sent_message)

    received_message = friend_input_thread.get(receive_timeout)
    assert received_message == sent_message

    friend_client.disconnect()
    test_client.disconnect()


@pytest.mark.skip
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.receivesInputMessages
def test_friend_to_module_routing_fi():

    test_client = connections.connect_test_module_client()
    test_client.enable_input_messages()
    friend_client = connections.connect_friend_module_client()

    test_input_thread = test_client.wait_for_input_event_async(friend_to_test_input)

    sent_message = test_utilities.max_random_string()
    friend_client.send_output_event(friend_to_test_output, sent_message)

    received_message = test_input_thread.get(receive_timeout)
    assert received_message == sent_message

    friend_client.disconnect()
    test_client.disconnect()


@pytest.mark.skip
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.callsSendOutputEvent
@pytest.mark.receivesInputMessages
def test_module_test_to_friend_and_back_fi():
    try:
        test_client = connections.connect_test_module_client()
        test_client.enable_input_messages()
        friend_client = connections.connect_friend_module_client()
        friend_client.enable_input_messages()

        test_input_thread = test_client.wait_for_input_event_async(friend_to_test_input)
        friend_input_thread = friend_client.wait_for_input_event_async(
            test_to_friend_input
        )
        disconnect_edgehub()
        sent_message = test_utilities.max_random_string()
        test_client.send_output_event(test_to_friend_output, sent_message)
        connect_edgehub()
        midpoint_message = friend_input_thread.get(receive_timeout)
        assert midpoint_message == sent_message

        second_sent_message = test_utilities.max_random_string()
        friend_client.send_output_event(friend_to_test_output, second_sent_message)

        received_message = test_input_thread.get(receive_timeout)
        assert received_message == second_sent_message

        friend_client.disconnect()
        test_client.disconnect()
    finally:
        restart_edgehub(hard=True)
