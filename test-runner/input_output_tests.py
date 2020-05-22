# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import sample_content
from horton_logging import logger


input_name_from_friend = "fromFriend"
output_name_to_friend = "toFriend"

sleep_time_for_listener_start = 10

telemetry_output_name = "telemetry"


class InputOutputTests(object):
    @pytest.fixture
    def output_name_to_test_client(self, client):
        return "to" + client.module_id

    @pytest.fixture
    def input_name_from_test_client(self, client):
        return "from" + client.module_id

    @pytest.mark.receivesInputMessages
    @pytest.mark.it("Can connect, enable input messages, and disconnect")
    async def test_inputoutput_connect_enable_input_messages_disconnect(self, client):
        await client.enable_input_messages()
        # BKTODO: Node breaks with edge amqpws without this.
        await asyncio.sleep(2)

    @pytest.mark.callsSendOutputEvent
    @pytest.mark.it("Can send an output message which gets routed to another module")
    async def test_inputoutput_module_to_friend_routing(
        self, client, friend, input_name_from_test_client
    ):
        payload = sample_content.make_message_payload()

        await friend.enable_input_messages()
        logger("messages enabled")

        friend_input_future = asyncio.ensure_future(
            friend.wait_for_input_event(input_name_from_test_client)
        )
        await asyncio.sleep(sleep_time_for_listener_start)
        logger("friend future created")

        await client.send_output_event(output_name_to_friend, payload)
        logger("message sent")

        received_message = await friend_input_future
        logger("received message")
        assert received_message.body == payload

    @pytest.mark.receivesInputMessages
    @pytest.mark.it("Can receive an input message which is routed from another module")
    async def test_inputoutput_friend_to_module_routing(
        self, client, friend, output_name_to_test_client
    ):
        payload = sample_content.make_message_payload()

        await client.enable_input_messages()

        # BKTODO Node bug.  Can't have overlapped register ops with AMQP
        await asyncio.sleep(sleep_time_for_listener_start)

        test_input_future = asyncio.ensure_future(
            client.wait_for_input_event(input_name_from_friend)
        )
        await asyncio.sleep(sleep_time_for_listener_start)

        await friend.send_output_event(output_name_to_test_client, payload)

        received_message = await test_input_future
        assert received_message.body == payload

    @pytest.mark.callsSendOutputEvent
    @pytest.mark.receivesInputMessages
    @pytest.mark.it(
        "Can send a message that gets routed to a friend and then receive a message in reply"
    )
    async def test_inputoutput_module_test_to_friend_and_back(
        self, client, friend, input_name_from_test_client, output_name_to_test_client
    ):

        payload = sample_content.make_message_payload()
        payload_2 = sample_content.make_message_payload()

        await friend.enable_input_messages()
        await client.enable_input_messages()

        # BKTODO Node bug.  Can't have overlapped register ops with AMQP
        await asyncio.sleep(sleep_time_for_listener_start)

        test_input_future = asyncio.ensure_future(
            client.wait_for_input_event(input_name_from_friend)
        )
        friend_input_future = asyncio.ensure_future(
            friend.wait_for_input_event(input_name_from_test_client)
        )
        await asyncio.sleep(sleep_time_for_listener_start)

        await client.send_output_event(output_name_to_friend, payload)

        midpoint_message = await friend_input_future
        assert midpoint_message.body == payload

        await friend.send_output_event(output_name_to_test_client, payload_2)

        received_message = await test_input_future
        assert received_message.body == payload_2

    @pytest.mark.callsSendOutputEvent
    @pytest.mark.it("Can send a message that gets routed to eventhub")
    async def test_inputoutput_module_output_routed_upstream(self, client, eventhub):
        payload = sample_content.make_message_payload()

        # start listening before we send
        await eventhub.connect()
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id, expected=payload)
        )

        await client.send_output_event(telemetry_output_name, payload)

        received_message = await received_message_future
        assert received_message is not None, "Message not received"
