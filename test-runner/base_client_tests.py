# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import logging

logger = logging.getLogger(__name__)


class BaseClientTests(object):
    @pytest.mark.it("Can connect and immediately disconnect")
    async def test_client_connect_disconnect(self, client):
        pass


# BKTODO: This should be folded into BaseClientTests, but we can't do that
# until we can get tags based on the client that's actually being tested.  Otherwise,
# we try to run these tests on the friend device when it might not be able to
# support this functionality.
class ConnectionStatusTests(object):
    @pytest.mark.uses_v2_connect_group
    @pytest.mark.it("Shows if the client is connected or disconnected")
    async def test_connection_status(self, client):

        assert client.get_connection_status() == "connected"

        client.disconnect2()
        assert client.get_connection_status() == "disconnected"

        client.connect2()
        assert client.get_connection_status() == "connected"
