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


invalid_symmetric_key_fields = [
    ("SharedAccessKey", "OPpcYRFtns6e9FCJIwhsNUbG0fHaUuB+AaUWUqy5kzg="),
    # ("HostName", "fakeFake.azure-devices.net"),
    ("DeviceId", "fakeDeviceId"),
]


def is_api_failure_exception(e):
    """
    return True if this exception is because of an API failure
    (as opposed to an msrest timeout, which is also a ClientRequestError)
    """
    # BKTODO: there needs to be a better adapter-specific way to map
    # wrapper exceptions into something the tests can use
    if "azure.iot.device" in str(e.__class__):
        return True
    else:
        return (
            type(e) == msrest.exceptions.ClientRequestError
            and type(e.inner_exception) == requests.exceptions.RetryError
        )


class RegressionTests(object):
    @pytest.mark.v2_connect_group
    @pytest.mark.it("Fails to connect if part of the connection string is wrong")
    @pytest.mark.parametrize(
        "field_name, new_field_value", invalid_symmetric_key_fields
    )
    async def test_regression_connect_fails_with_corrupt_symmetric_key(
        self, client, field_name, new_field_value
    ):

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field_name] = new_field_value

        client.create_from_connection_string_sync(
            client.settings.transport,
            connection_string.dictionary_to_connection_string(cs_fields),
            connections.get_ca_cert(client.settings),
        )

        with pytest.raises(Exception) as e:
            await client.connect2()
        assert is_api_failure_exception(e._excinfo[1])

    @pytest.mark.v2_connect_group
    @pytest.mark.it("Fails to send a message if part of the connection string is wrong")
    @pytest.mark.parametrize(
        "field_name, new_field_value", invalid_symmetric_key_fields
    )
    async def test_regression_send_message_fails_with_corrupt_symmetric_key(
        self, client, field_name, new_field_value
    ):

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        payload = sample_content.make_message_payload()

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field_name] = new_field_value

        client.create_from_connection_string_sync(
            client.settings.transport,
            connection_string.dictionary_to_connection_string(cs_fields),
            connections.get_ca_cert(client.settings),
        )

        with pytest.raises(Exception):
            await client.send_event(payload)
