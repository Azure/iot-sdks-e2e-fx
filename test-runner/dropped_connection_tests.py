# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import datetime
from twin_tests import wait_for_reported_properties_update
from sample_content import next_random_string
from horton_settings import settings


telemetry_output_name = "telemetry"
output_name_to_friend = "toFriend"


class DroppedConnectionTestsBase(object):
    @pytest.mark.it("Shows if the client is connected or disconnected")
    async def test_connection_status(self, client):

        assert await client.get_connection_status() == "connected"

        await client.disconnect2()
        assert await client.get_connection_status() == "disconnected"

        await client.connect2()
        assert await client.get_connection_status() == "connected"

    @pytest.mark.it("Can reconnect after dropped connection")
    async def test_client_dropped_connection(
        self,
        client,
        test_module_wrapper_api,
        drop_mechanism,
        logger,
        test_module_transport,
    ):
        await self.start_dropping(
            test_module_wrapper_api=test_module_wrapper_api,
            logger=logger,
            drop_mechanism=drop_mechanism,
            test_module_transport=test_module_transport,
        )
        await self.wait_for_disconnection_event(client=client, logger=logger)
        await asyncio.sleep(10)
        await self.stop_dropping(
            test_module_wrapper_api=test_module_wrapper_api, logger=logger
        )
        await self.wait_for_reconnection_event(client=client, logger=logger)


class DroppedConnectionTestsTelemetry(object):
    @pytest.mark.it("Can reliably send an event")
    async def test_client_dropped_send_event(
        self, client, before_api_call, after_api_call, eventhub, test_payload
    ):
        start_listening_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=30
        )  # start listning early because of clock skew

        await before_api_call()
        send_future = asyncio.ensure_future(client.send_event(test_payload))
        await after_api_call()

        # wait for the send to complete, and verify that it arrvies
        await send_future

        await eventhub.connect(offset=start_listening_time)
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id, expected=test_payload)
        )
        received_message = await received_message_future
        assert received_message is not None, "Message not received"

    @pytest.mark.it("Can reliably send 5 events")
    @pytest.mark.skip("#BKTODO")
    async def test_client_dropped_send_event_5x(self):
        pass


class DroppedConnectionTestsC2d(object):
    @pytest.mark.it("Can reliably reveive c2d (1st-time possible subscribe)")
    async def test_dropped_c2d_1st_call(
        self, client, service, before_api_call, after_api_call, test_string, logger
    ):
        await client.enable_c2d()

        await before_api_call()
        test_input_future = asyncio.ensure_future(client.wait_for_c2d_message())
        await after_api_call()

        await asyncio.sleep(30)  # long time necessary to let subscribe happen
        logger("transport connected.  Sending C2D")

        await service.send_c2d(client.device_id, test_string)

        logger("C2D sent.  Waiting for response")

        received_message = await test_input_future
        assert received_message == test_string

    @pytest.mark.it("Can reliably reveive c2d (2nd-time)")
    async def test_dropped_c2d_2nd_call(
        self, client, service, before_api_call, after_api_call, logger
    ):

        # 1st call
        test_string = next_random_string("dropped-c2d")

        await client.enable_c2d()

        test_input_future = asyncio.ensure_future(client.wait_for_c2d_message())
        await service.send_c2d(client.device_id, test_string)
        received_message = await test_input_future
        assert received_message == test_string

        # 2nd call
        test_string = next_random_string("dropped-c2d")

        await before_api_call()
        test_input_future = asyncio.ensure_future(client.wait_for_c2d_message())
        await after_api_call()

        await service.send_c2d(client.device_id, test_string)

        logger("Awaiting input")
        received_message = await test_input_future
        assert received_message == test_string


class DroppedConnectionTestsTwin(object):
    @pytest.mark.it(
        "Can reliably update reported properties (1st time - possible subscribe)"
    )
    async def test_twin_dropped_reported_properties_publish_1st_call(
        self,
        client,
        before_api_call,
        after_api_call,
        logger,
        registry,
        sample_reported_props,
    ):

        props = sample_reported_props()

        await before_api_call()
        patch_future = asyncio.ensure_future(client.patch_twin(props))
        await after_api_call()

        await patch_future
        await wait_for_reported_properties_update(
            reported_properties_sent=props,
            client=client,
            registry=registry,
            logger=logger,
        )

    @pytest.mark.it("Can reliably update reported properties (2nd time)")
    async def test_twin_dropped_reported_properties_publish_2nd_call(
        self,
        client,
        before_api_call,
        after_api_call,
        logger,
        registry,
        sample_reported_props,
    ):
        await client.patch_twin(sample_reported_props())

        await before_api_call()
        props = sample_reported_props()
        patch_future = asyncio.ensure_future(client.patch_twin(props))
        await after_api_call()

        await patch_future
        await wait_for_reported_properties_update(
            reported_properties_sent=props,
            client=client,
            registry=registry,
            logger=logger,
        )

    @pytest.mark.it("Can reliably get the twin (1st call - possible subscribe)")
    async def test_twin_dropped_get_twin_1st_call(
        self, client, before_api_call, after_api_call
    ):
        await before_api_call()
        get_twin_future = asyncio.ensure_future(client.get_twin())
        await after_api_call()

        twin = await get_twin_future
        assert twin["properties"]["desired"]["$version"]

    @pytest.mark.it("Can reliably get the twin (2nd call)")
    async def test_twin_dropped_get_twin_2nd_call(
        self, client, before_api_call, after_api_call
    ):
        await client.get_twin()

        await before_api_call()
        get_twin_future = asyncio.ensure_future(client.get_twin())
        await after_api_call()

        twin = await get_twin_future
        assert twin["properties"]["desired"]["$version"]

    @pytest.mark.it(
        "Can reliably receive a desired property patch (1st call - possible subscribe)"
    )
    @pytest.mark.skip("#BKTODO")
    async def test_twin_dropped_wait_for_desired_properties_patch_1st_call(self):
        pass

    @pytest.mark.it("Can reliably receive a desired property patch (2nd call)")
    @pytest.mark.skip("#BKTODO")
    async def test_twin_dropped_wait_for_desired_properties_patch_2nd_call(self):
        pass


class DroppedConnectionTestsInputOutput(object):
    @pytest.fixture
    def input_name_from_test_client(self, client):
        return "from" + client.module_id

    @pytest.mark.it("Can reliably send an output event")
    async def test_dropped_send_output(
        self,
        client,
        friend,
        input_name_from_test_client,
        before_api_call,
        after_api_call,
        sample_payload,
    ):
        test_payload = sample_payload()

        friend_input_future = asyncio.ensure_future(
            friend.wait_for_input_event(input_name_from_test_client)
        )

        await before_api_call()
        send_future = asyncio.ensure_future(
            client.send_output_event(output_name_to_friend, test_payload)
        )
        await after_api_call()

        # wait for the send to complete, and verify that it arrvies
        await send_future
        received_message = await friend_input_future
        print("received message")
        assert received_message == test_payload

    @pytest.mark.it("Can reliably send 5 output events")
    async def test_dropped_send_output_5x(
        self, client, eventhub, sample_payload, logger, before_api_call, after_api_call
    ):
        start_listening_time = datetime.datetime.utcnow() - datetime.timedelta(
            seconds=30
        )  # start listning early because of clock skew
        payloads = [sample_payload() for x in range(0, 5)]
        futures = []

        await before_api_call()
        for payload in payloads:
            futures.append(
                asyncio.ensure_future(
                    client.send_output_event(telemetry_output_name, payload)
                )
            )
        await after_api_call()

        # wait for the send to complete, and verify that it arrvies
        await asyncio.gather(*futures)

        logger("All messages sent.  Awaiting reception")

        logger("connecting eventhub")
        await eventhub.connect(offset=start_listening_time)
        receive_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id)
        )

        while len(payloads):
            received_message = await receive_future

            if received_message in payloads:
                logger(
                    "Received expected message: {}, removing from list".format(
                        received_message
                    )
                )
                payloads.remove(received_message)
            else:
                logger("Received unexpected message: {}".format(received_message))

            if len(payloads):
                receive_future = asyncio.ensure_future(
                    eventhub.wait_for_next_event(client.device_id)
                )

    @pytest.mark.it("Can reliably receive an input event")
    @pytest.mark.skip("#BKTODO")
    async def test_dropped_receive_input(self):
        pass

    @pytest.mark.it("Can reliably receive 5 input events")
    @pytest.mark.skip("#BKTODO")
    async def test_dropped_receive_input_5x(self):
        pass


class DroppedConnectionIoTHubDeviceTests(
    DroppedConnectionTestsBase,
    DroppedConnectionTestsTelemetry,
    DroppedConnectionTestsTwin,
    DroppedConnectionTestsC2d,
):
    pass


class DroppedConnectionIoTHubModuleTests(
    DroppedConnectionTestsBase,
    DroppedConnectionTestsTelemetry,
    DroppedConnectionTestsTwin,
):
    pass


class DroppedConnectionEdgeHubModuleTests(
    DroppedConnectionTestsBase,
    DroppedConnectionTestsTelemetry,
    DroppedConnectionTestsInputOutput,
    DroppedConnectionTestsTwin,
):
    pass
