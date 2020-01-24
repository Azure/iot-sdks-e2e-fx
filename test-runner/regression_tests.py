# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import limitations
import sample_content
from horton_logging import logger


class RegressionTests(object):
    @pytest.mark.v2_connect_group
    @pytest.mark.it("Fails to send a message if the symmetric key is incorrect")
    async def test_send_message_fails_with_corrupt_symmetric_key(self, client):

        if not limitations.uses_shared_key_auth(client):
            pytest.skip("client is not using shared key auth")

        payload = sample_content.make_message_payload()

        await client.send_event(payload)
