# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import logging

logger = logging.getLogger(__name__)


class BaseClientTests(object):
    @pytest.mark.it("Can connect and immediately disconnect")
    def test_client_connect_disconnect(self, client):
        pass

    @pytest.mark.uses_connection_status
    @pytest.mark.uses_connect_v2
    @pytest.mark.it("Shows if the client is connected or disconnected")
    def test_connection_status(self, client):

        assert client.get_connection_status() == "connected"

        client.disconnect2()
        assert client.get_connection_status() == "disconnected"

        client.connect2()
        assert client.get_connection_status() == "connected"
