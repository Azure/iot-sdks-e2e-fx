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


def corrupt_string(source_string):
    return "AA" + source_string


class RegressionTests(object):
    @pytest.mark.v2_connect_group
    @pytest.mark.it("Fails to send a message if the symmetric key is incorrect")
    @pytest.mark.parametrize("field", ["SharedAccessKey", "HostName", "DeviceId"])
    async def test_regression_send_message_fails_with_corrupt_symmetric_key(
        self, client, field
    ):

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        payload = sample_content.make_message_payload()

        cs_fields = connection_string.connection_string_to_dictionary(
            client.settings.connection_string
        )
        cs_fields[field] = corrupt_string(cs_fields[field])

        client.create_from_connection_string_sync(
            client.settings.transport,
            connection_string.dictionary_to_connection_string(cs_fields),
            connections.get_ca_cert(client.settings),
        )

        with pytest.raises(Exception):
            await client.send_event(payload)
