# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
from twin_tests import wait_for_reported_properties_update
from sample_content import next_random_string


telemetry_output_name = "telemetry"


class MotherOfAllBaseClasses(object):
    @pytest.fixture(
        params=[
            pytest.param("DROP", id="Drop using iptables DROP"),
            # pytest.param("REJECT", id="Drop using iptables REJECT"),
        ]
    )
    def drop_mechanism(self, request):
        """
        Parametrized fixture which lets our tests run against the full set
        of dropping mechanisms.  Every test in this file will run using each value
        for this array of parameters.
        """
        return request.param

    @pytest.fixture(autouse=True)
    def always_reconnect(self, request, logger, test_module_wrapper_api):
        # if this test is going to drop packets, add a finalizer to make sure we always stop
        # stop dropping it when we're done.  Calling network_connect_sync twice in a row is allowed.
        def always_reconnect():
            logger("in finalizer: no longer dropping packets")
            test_module_wrapper_api.network_reconnect_sync()

        request.addfinalizer(always_reconnect)

    async def start_dropping(self, *, test_module_wrapper_api, logger, drop_mechanism):
        logger("start drop packets")
        await test_module_wrapper_api.network_disconnect(drop_mechanism)

    async def wait_for_disconnection_event(self, *, client, logger):
        status = await client.get_connection_status()
        assert status == "connected"

        logger("waiting for client disconnection event")
        status = await client.wait_for_connection_status_change()
        assert status == "disconnected"
        logger("client disconnection event received")

    async def stop_dropping(self, *, test_module_wrapper_api, logger):
        logger("stop dropping packets")
        await test_module_wrapper_api.network_reconnect()

    async def wait_for_reconnection_event(self, *, client, logger):
        logger("waiting for client reconnection event")
        status = await client.wait_for_connection_status_change()
        assert status == "connected"
        logger("client reconnection event received")


class CallMethodBeforeOnDisconnected(MotherOfAllBaseClasses):
    @pytest.fixture
    def before_api_call(self, drop_mechanism, test_module_wrapper_api, logger):
        async def func():
            await self.start_dropping(
                test_module_wrapper_api=test_module_wrapper_api,
                logger=logger,
                drop_mechanism=drop_mechanism,
            )

        return func

    @pytest.fixture
    def after_api_call(self, client, test_module_wrapper_api, logger):
        async def func():
            await self.wait_for_disconnection_event(client=client, logger=logger)
            await asyncio.sleep(10)
            await self.stop_dropping(
                test_module_wrapper_api=test_module_wrapper_api, logger=logger
            )
            await self.wait_for_reconnection_event(client=client, logger=logger)

        return func


class CallMethodAfterOnDisconencted(object):
    pass


class CallMethodWhileDisconnectedNetworkAvailable(object):
    pass


class CallMethodWhileDisconnectedNetworkNotAvailable(object):
    pass


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
        self, client, test_module_wrapper_api, drop_mechanism, logger
    ):
        await self.start_dropping(
            test_module_wrapper_api=test_module_wrapper_api,
            logger=logger,
            drop_mechanism=drop_mechanism,
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
        # start listening before we send
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id, expected=test_payload)
        )

        await before_api_call()
        send_future = asyncio.ensure_future(client.send_event(test_payload))
        await after_api_call()

        # wait for the send to complete, and verify that it arrvies
        await send_future
        received_message = await received_message_future
        assert received_message is not None, "Message not received"


class DroppedConnectionTestsC2d(object):
    @pytest.mark.it("Does not leak if a C2D never arrives")
    async def test_client_c2d_timeout(self, client):
        pytest.skip("our code leaks right now.")

        asyncio.ensure_future(client.wait_for_c2d_message())
        # this future should never complete, but we don't care.
        # this test will fail in the cleanup when the test wrapper has
        # a chance to look for leaks

    @pytest.mark.it("Can reliably subscribe to the C2d topic")
    async def test_client_dropped_c2d_subscribe(
        self, client, service, before_api_call, after_api_call, test_string
    ):
        await before_api_call()
        subscribe_future = asyncio.ensure_future(client.enable_c2d())
        await after_api_call()

        await subscribe_future
        test_input_future = asyncio.ensure_future(client.wait_for_c2d_message())
        await asyncio.sleep(2)  # wait for receive pipeline to finish setting up

        await service.send_c2d(client.device_id, test_string)

        received_message = await test_input_future
        assert received_message == test_string

    @pytest.mark.it("Can reliably reveive c2d (1st-time possible subscribe)")
    async def test_client_dropped_c2d_1st_call(
        self, client, service, before_api_call, after_api_call, test_string
    ):
        if isinstance(self, CallMethodBeforeOnDisconnected):
            # paho doesn't retry subscribe so this fails
            pytest.skip()

        await client.enable_c2d()

        await before_api_call()
        test_input_future = asyncio.ensure_future(client.wait_for_c2d_message())
        await after_api_call()

        await service.send_c2d(client.device_id, test_string)

        print("Awaiting input")
        received_message = await test_input_future
        assert received_message == test_string

    @pytest.mark.it("Can reliably reveive c2d (2nd-time)")
    async def test_client_dropped_c2d_2nd_call(
        self, client, service, before_api_call, after_api_call
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

        print("Awaiting input")
        received_message = await test_input_future
        assert received_message == test_string


class DroppedConnectionTestsTwin(object):
    @pytest.mark.it(
        "Can reliably update reported properties (1st time - possible subscribe)"
    )
    async def test_client_dropped_reported_properties_publish_1st_call(
        self,
        client,
        before_api_call,
        after_api_call,
        logger,
        registry,
        sample_reported_props,
    ):
        if isinstance(self, CallMethodBeforeOnDisconnected):
            # paho doesn't retry subscribe so this fails
            pytest.skip()

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
    async def test_client_dropped_reported_properties_publish_2nd_call(
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


class DroppedConnectionTestsInputOutput(object):
    @pytest.mark.it("Can rerliably send an output event")
    async def test_client_dropped_send_output(
        self, client, before_api_call, after_api_call, eventhub, test_payload
    ):
        receive_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id, expected=test_payload)
        )

        await before_api_call()
        send_future = asyncio.ensure_future(
            client.send_output_event(telemetry_output_name, test_payload)
        )
        await after_api_call()

        # wait for the send to complete, and verify that it arrvies
        await send_future
        received_message = await receive_message_future
        assert received_message is not None, "Message not received"


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
