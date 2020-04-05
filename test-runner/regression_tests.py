# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import limitations
import sample_content
from horton_logging import logger
import connections
import connection_string
import requests
import msrest
import input_output_tests
import telemetry_tests


invalid_symmetric_key_fields = [
    pytest.param("SharedAccessKey", "aGlsbGJpbGx5IHN1bnJpc2UK"),
    pytest.param("HostName", "fakeFake.azure-devices.net"),
    pytest.param("DeviceId", "fakeDeviceId"),
]


def is_api_failure_exception(e):
    """
    return True if this exception is because of an API failure
    (as opposed to an msrest timeout, which is also a ClientRequestError)
    """
    # BKTODO: there needs to be a better adapter-specific way to map
    # wrapper exceptions into something the tests can use
    if (
        type(e) == msrest.exceptions.ClientRequestError
        and type(e.inner_exception) == requests.exceptions.ReadTimeout
    ):
        return False
    else:
        return True


class RegressionTests(object):
    @pytest.fixture(
        params=[
            pytest.param("DROP", id="Drop using iptables DROP"),
            pytest.param("REJECT", id="Drop using iptables REJECT"),
        ]
    )
    def drop_mechanism(self, request):
        """
        Parametrized fixture which lets our tests run against the full set
        of dropping mechanisms.  Every test in this file will run using each value
        for this array of parameters.
        """
        return request.param

    @pytest.mark.it("Fails to connect if part of the connection string is wrong")
    @pytest.mark.parametrize(
        "field_name, new_field_value", invalid_symmetric_key_fields
    )
    async def test_regression_connect_fails_with_corrupt_connection_string(
        self, client, field_name, new_field_value
    ):
        limitations.only_run_test_for(client, "pythonv2")

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field_name] = new_field_value

        client.destroy_sync()
        client.create_from_connection_string_sync(
            client.settings.transport,
            connection_string.dictionary_to_connection_string(cs_fields),
            connections.get_ca_cert(client.settings),
        )

        with pytest.raises(Exception) as e:
            await client.connect2()
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it("Fails to send a message if part of the connection string is wrong")
    @pytest.mark.parametrize(
        "field_name, new_field_value", invalid_symmetric_key_fields
    )
    async def test_regression_send_message_fails_with_corrupt_connection_string(
        self, client, field_name, new_field_value
    ):
        limitations.only_run_test_for(client, "pythonv2")

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        payload = sample_content.make_message_payload()

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field_name] = new_field_value

        client.destroy_sync()
        client.create_from_connection_string_sync(
            client.settings.transport,
            connection_string.dictionary_to_connection_string(cs_fields),
            connections.get_ca_cert(client.settings),
        )

        with pytest.raises(Exception) as e:
            await client.send_event(payload)
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it("fails to send messages over 256 kb in size")
    async def test_regression_send_message_fails_with_message_over_256K(self, client):
        limitations.only_run_test_for(client, "pythonv2")

        big_payload = sample_content.make_message_payload(size=257 * 1024)

        with pytest.raises(Exception) as e:
            await client.send_event(big_payload)
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it("fails to send output messages over 256 kb in size")
    async def test_regression_send_output_message_fails_with_message_over_256K(
        self, client
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.only_run_test_on_iotedge_module(client)

        big_payload = sample_content.make_message_payload(size=257 * 1024)

        with pytest.raises(Exception) as e:
            await client.send_output_event(
                input_output_tests.output_name_to_friend, big_payload
            )
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it(
        "does not break the client on failure sending messages over 256 kb in size"
    )
    async def test_regression_send_message_big_message_doesnt_break_client(
        self, client, eventhub
    ):
        limitations.only_run_test_for(client, "pythonv2")

        big_payload = sample_content.make_message_payload(size=257 * 1024)
        small_payload = sample_content.make_message_payload()

        await eventhub.connect()

        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id, expected=small_payload)
        )

        with pytest.raises(Exception):
            await client.send_event(big_payload)

        await client.send_event(small_payload)

        received_message = await received_message_future
        assert received_message is not None, "Message not received"

    @pytest.mark.it(
        "fails a connect operation if connection fails for the first time connecting"
    )
    async def test_regression_bad_connection_fail_first_connection(
        self, net_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()
        if not client.settings.capabilities.new_python_reconnect:
            pytest.skip("waiting for python ReconnectStage changes")

        await net_control.disconnect(drop_mechanism)

        with pytest.raises(Exception) as e:
            await client.connect2()

        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it(
        "fails a send_event operation if connection fails for the first time connecting"
    )
    async def test_regression_bad_connection_fail_first_send_event(
        self, net_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()
        if not client.settings.capabilities.new_python_reconnect:
            pytest.skip("waiting for python ReconnectStage changes")

        await net_control.disconnect(drop_mechanism)

        payload = sample_content.make_message_payload()

        with pytest.raises(Exception) as e:
            await client.send_event(payload)

        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it(
        "retries a connect operation if connection fails for the second time connecting"
    )
    async def test_regression_bad_connection_retry_second_connection(
        self, net_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()

        await client.connect2()
        await client.disconnect2()

        await net_control.disconnect(drop_mechanism)

        connect_future = asyncio.ensure_future(client.connect2())

        await asyncio.sleep(2)

        await net_control.reconnect()

        await connect_future

    @pytest.mark.it(
        "retries a send_event operation if connection fails for the second time connecting"
    )
    async def test_regression_bad_connection_retry_second_send_event(
        self, net_control, client, drop_mechanism, eventhub
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()

        await client.connect2()
        await client.disconnect2()

        payload = sample_content.make_message_payload()

        await eventhub.connect()
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id, expected=payload)
        )

        await net_control.disconnect(drop_mechanism)

        send_future = asyncio.ensure_future(client.send_event(payload))

        await asyncio.sleep(1)

        await net_control.reconnect()

        await send_future
        received_message = await received_message_future

        assert received_message

    @pytest.mark.it(
        "Can retry multiple conenct operations while the network is disconnected"
    )
    async def test_regression_bad_connection_retry_multiple_connections(
        self, net_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()

        await client.connect2()
        await client.disconnect2()

        await net_control.disconnect(drop_mechanism)

        connect_future_1 = asyncio.ensure_future(client.connect2())
        connect_future_2 = asyncio.ensure_future(client.connect2())
        connect_future_3 = asyncio.ensure_future(client.connect2())

        await asyncio.sleep(5)

        await net_control.reconnect()

        await connect_future_1
        await connect_future_2
        await connect_future_3

    @pytest.mark.it(
        "Enables automatic reconnection even if connect is not called directly"
    )
    async def test_regression_autoconnect_without_calling_connect(
        self, net_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()
        if not client.settings.capabilities.new_python_reconnect:
            pytest.skip("waiting for python ReconnectStage changes")

        payload = sample_content.make_message_payload()
        await client.send_event(payload)

        status = await client.get_connection_status()
        assert status == "connected"

        await net_control.disconnect(drop_mechanism)

        await client.wait_for_connection_status_change("disconnected")

        await net_control.reconnect()

        await client.wait_for_connection_status_change("connected")
        assert status == "connected"

    @pytest.mark.it("Can retry send_event with different failure conditions")
    async def test_regression_reconnect_send_event_different_timing(
        self, net_control, client, drop_mechanism, eventhub
    ):
        payloads = []
        send_futures = []

        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()
        if not client.settings.capabilities.new_python_reconnect:
            pytest.skip("waiting for python ReconnectStage changes")

        logger("connecting")
        await client.connect2()

        logger("unplugging network")
        await net_control.disconnect(drop_mechanism)

        # start listening before we send
        await eventhub.connect()
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id)
        )

        logger(
            "sending 2 messages before the client realizes the network was unplugged"
        )
        for _ in range(0, 2):
            telemetry_tests.ensure_send_telemetry_message(
                client=client, payloads=payloads, send_futures=send_futures
            )

        logger("wait for the client to realize the network was unplugged")
        await client.wait_for_connection_status_change("disconnected")

        logger("send 2 more messages")
        for _ in range(0, 2):
            telemetry_tests.ensure_send_telemetry_message(
                client=client, payloads=payloads, send_futures=send_futures
            )

        logger("reconnect the network")
        await net_control.reconnect()

        logger("waiting for all messages to send")
        await asyncio.gather(*send_futures)

        logger("waiting for events to arrive at eventhub")
        await telemetry_tests.wait_for_all_telemetry_messages_to_arrive(
            received_message_future=received_message_future,
            payloads=payloads,
            eventhub=eventhub,
            client=client,
        )

    @pytest.mark.skip("Fails because packets are still 'in flight' when disconnecting")
    @pytest.mark.it("Can fail send_event calls by manually disconnecting")
    async def test_regression_disconnect_cancels_send_event(
        self, net_control, client, drop_mechanism
    ):
        payloads = []
        send_futures = []

        limitations.only_run_test_for(client, "pythonv2")
        limitations.skip_if_no_net_control()
        if not client.settings.capabilities.new_python_reconnect:
            pytest.skip("waiting for python ReconnectStage changes")

        logger("connecting")
        await client.connect2()

        logger("unplugging network")
        await net_control.disconnect(drop_mechanism)

        logger(
            "sending 2 messages before the client realizes the network was unplugged"
        )
        for _ in range(0, 2):
            telemetry_tests.ensure_send_telemetry_message(
                client=client, payloads=payloads, send_futures=send_futures
            )

        logger("wait for the client to realize the network was unplugged")
        await client.wait_for_connection_status_change("disconnected")

        logger("send 2 more messages")
        for _ in range(0, 2):
            telemetry_tests.ensure_send_telemetry_message(
                client=client, payloads=payloads, send_futures=send_futures
            )

        logger("forcing a disconnection")
        await client.disconnect2()

        logger("verifying that all of our sends failed")
        for send_future in send_futures:
            with pytest.raises(Exception):
                await send_future
        logger("all sends failed")
