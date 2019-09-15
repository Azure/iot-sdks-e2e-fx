# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import time
from models import HubEvent
import sample_content
import utilities


input_name_from_friend = "fromFriend"
output_name_to_friend = "toFriend"

receive_timeout = 60

telemetry_output_name = "telemetry"
loopback_output_name = "loopout"
loopback_input_name = "loopin"


class InputOutputTests(object):
    @pytest.fixture
    def output_name_to_test_client(self, client):
        return "to" + client.module_id

    @pytest.fixture
    def input_name_from_test_client(self, client):
        return "from" + client.module_id

    @pytest.mark.receivesInputMessages
    @pytest.mark.it("Can connect, enable input messages, and disconnect")
    def test_module_client_connect_enable_input_messages_disconnect(self, client):
        client.enable_input_messages()
        # BKTODO: Node breaks with edge amqpws without this.
        time.sleep(2)

    @pytest.mark.callsSendOutputEvent
    @pytest.mark.it("Can send an output message which gets routed to another module")
    def test_module_to_friend_routing(
        self, client, friend, test_string, input_name_from_test_client
    ):

        friend.enable_input_messages()

        friend_input_thread = friend.wait_for_input_event_async(
            input_name_from_test_client
        )

        client.send_output_event(output_name_to_friend, test_string)

        received_message = friend_input_thread.get(receive_timeout)
        assert received_message == test_string

    @pytest.mark.parametrize("body", sample_content.telemetry_test_objects)
    @pytest.mark.uses_new_message_format
    @pytest.mark.callsSendOutputEvent
    @pytest.mark.it(
        "Can send an output message which gets routed to another module using new Horton HubEvent"
    )
    def test_module_to_friend_routing_hubevent(
        self, client, friend, input_name_from_test_client, body
    ):
        friend.enable_input_messages()

        friend_input_thread = friend.wait_for_input_event_async(
            input_name_from_test_client
        )

        sent_message = HubEvent(body)
        client.send_output_event(output_name_to_friend, sent_message.convert_to_json())

        received_message = friend_input_thread.get(receive_timeout)
        assert utilities.json_is_same(received_message, sent_message.body)

    @pytest.mark.receivesInputMessages
    @pytest.mark.it("Can receive an input message which is routed from another module")
    def test_friend_to_module_routing(
        self, client, friend, test_string, output_name_to_test_client
    ):

        client.enable_input_messages()

        test_input_thread = client.wait_for_input_event_async(input_name_from_friend)

        friend.send_output_event(output_name_to_test_client, test_string)

        received_message = test_input_thread.get(receive_timeout)
        assert received_message == test_string

    @pytest.mark.callsSendOutputEvent
    @pytest.mark.receivesInputMessages
    @pytest.mark.it(
        "Can send a message that gets routed to a friend and then receive a message in reply"
    )
    def test_module_test_to_friend_and_back(
        self,
        client,
        friend,
        test_string,
        test_string_2,
        input_name_from_test_client,
        output_name_to_test_client,
    ):

        client.enable_input_messages()
        friend.enable_input_messages()

        test_input_thread = client.wait_for_input_event_async(input_name_from_friend)
        friend_input_thread = friend.wait_for_input_event_async(
            input_name_from_test_client
        )

        client.send_output_event(output_name_to_friend, test_string)

        midpoint_message = friend_input_thread.get(receive_timeout)
        assert midpoint_message == test_string

        friend.send_output_event(output_name_to_test_client, test_string_2)

        received_message = test_input_thread.get(receive_timeout)
        assert received_message == test_string_2

    @pytest.mark.callsSendOutputEvent
    @pytest.mark.timeout(
        timeout=180
    )  # extra timeout in case eventhub needs to retry due to resource error
    @pytest.mark.it("Can send a message that gets routed to eventhub")
    def test_module_output_routed_upstream(
        self, client, eventhub, test_object_stringified
    ):

        client.send_output_event(telemetry_output_name, test_object_stringified)

        received_message = eventhub.wait_for_next_event(
            client.device_id, expected=test_object_stringified
        )
        assert received_message is not None, "Message not received"

    @pytest.mark.parametrize("body", sample_content.telemetry_test_objects)
    @pytest.mark.uses_new_message_format
    @pytest.mark.callsSendOutputEvent
    @pytest.mark.timeout(
        timeout=180
    )  # extra timeout in case eventhub needs to retry due to resource error
    @pytest.mark.it(
        "Can send a message that gets routed to eventhub using the new Horton HubEvent"
    )
    def test_module_output_routed_upstream_hubevent(self, client, eventhub, body):

        sent_message = HubEvent(body)
        client.send_output_event(telemetry_output_name, sent_message.convert_to_json())

        received_message = eventhub.wait_for_next_event(
            client.device_id, expected=sent_message.body
        )
        assert received_message is not None, "Message not received"

    @pytest.mark.callsendOutputMessage
    @pytest.mark.receivesInputMessages
    @pytest.mark.handlesLoopbackMessages
    @pytest.mark.it("Can send a message to itself")
    def test_module_input_output_loopback(self, client, test_string, logger):
        client.enable_input_messages()

        input_thread = client.wait_for_input_event_async(loopback_input_name)

        # give the registration a chance to take place
        time.sleep(2)

        client.send_output_event(loopback_output_name, test_string)

        received_message = input_thread.get(receive_timeout)
        logger("input message arrived")
        logger("expected message: " + str(test_string))
        logger("received message: " + str(received_message))
        assert received_message == test_string

    @pytest.mark.parametrize("body", sample_content.telemetry_test_objects)
    @pytest.mark.uses_new_message_format
    @pytest.mark.callsendOutputMessage
    @pytest.mark.receivesInputMessages
    @pytest.mark.handlesLoopbackMessages
    @pytest.mark.it("Can send a message to itself using the new Horton HubEvent")
    def test_module_input_output_loopback_hubevent(self, client, body, logger):
        client.enable_input_messages()

        input_thread = client.wait_for_input_event_async(loopback_input_name)

        # give the registration a chance to take place
        time.sleep(2)

        sent_message = HubEvent(body)
        client.send_output_event(loopback_output_name, sent_message.convert_to_json())

        received_message = input_thread.get(receive_timeout)
        logger("input message arrived")
        logger("expected message: " + str(body))
        logger("received message: " + str(received_message))
        assert utilities.json_is_same(sent_message.body, received_message)
