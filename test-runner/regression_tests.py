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
        limitations.only_run_test_for(client, ["node", "pythonv2"])

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field_name] = new_field_value

        await client.destroy()
        await client.create_from_connection_string(
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
        limitations.only_run_test_for(client, ["node", "pythonv2"])

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        payload = sample_content.make_message_payload()

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field_name] = new_field_value

        await client.destroy()
        await client.create_from_connection_string(
            client.settings.transport,
            connection_string.dictionary_to_connection_string(cs_fields),
            connections.get_ca_cert(client.settings),
        )

        with pytest.raises(Exception) as e:
            if limitations.needs_manual_connect(client):
                await client.connect2()
            await client.send_event(payload)
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it("fails to send messages over 256 kb in size")
    async def test_regression_send_message_fails_with_message_over_256K(self, client):
        limitations.only_run_test_for(client, ["node", "pythonv2"])
        if limitations.needs_manual_connect(client):
            await client.connect2()

        big_payload = sample_content.make_message_payload(size=257 * 1024)

        with pytest.raises(Exception) as e:
            await client.send_event(big_payload)
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it("fails to send output messages over 256 kb in size")
    async def test_regression_send_output_message_fails_with_message_over_256K(
        self, client
    ):
        limitations.only_run_test_for(client, ["node", "pythonv2"])
        limitations.only_run_test_on_iotedge_module(client)
        if limitations.needs_manual_connect(client):
            await client.connect2()

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
        limitations.only_run_test_for(client, ["node", "pythonv2"])

        big_payload = sample_content.make_message_payload(size=257 * 1024)
        small_payload = sample_content.make_message_payload()

        await eventhub.connect()
        if limitations.needs_manual_connect(client):
            await client.connect2()

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
        self, system_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, ["node", "pythonv2"])
        limitations.skip_if_no_system_control()

        await system_control.disconnect_network(drop_mechanism)

        with pytest.raises(Exception) as e:
            await client.connect2()

        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.it(
        "fails a send_event operation if connection fails for the first time connecting"
    )
    async def test_regression_bad_connection_fail_first_send_event(
        self, system_control, client, drop_mechanism
    ):
        limitations.only_run_test_for(client, ["node", "pythonv2"])
        limitations.skip_if_no_system_control()

        await system_control.disconnect_network(drop_mechanism)

        payload = sample_content.make_message_payload()

        with pytest.raises(Exception) as e:
            if limitations.needs_manual_connect(client):
                await client.connect2()
            await client.send_event(payload)

        assert is_api_failure_exception(e._excinfo[1])


    @pytest.mark.it("Lets us have a short keepalive interval")
    @pytest.mark.timeout(45)
    async def test_keepalive_interval(self, client, system_control, drop_mechanism):
        # We want the keepalive to be low to make these tests fast.  This
        # test is marked with a 45 second timeout.  Keepalive should be closer
        # to 10 seconds, so 45 to connect and notice the drop should be enough
        limitations.only_run_test_for(client, ["pythonv2"])
        limitations.skip_if_no_system_control()

        await client.connect2()

        await system_control.disconnect_network(drop_mechanism)
        await client.wait_for_connection_status_change("disconnected")

        await system_control.reconnect_network()
