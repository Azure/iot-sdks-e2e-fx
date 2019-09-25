# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import logging
import time

logger = logging.getLogger(__name__)

all_disconnection_types = [
    pytest.param("DROP", id="DROP"),
    pytest.param("REJECT", id="REJECT"),
]


class RetryTests(object):
    @pytest.mark.asyncio
    @pytest.mark.uses_v2_connect_group
    @pytest.mark.it("Can reconnect after dropped connection")
    @pytest.mark.timeout(300)
    @pytest.mark.parametrize("disconnection_type", all_disconnection_types)
    async def test_client_dropped_connection(
        self, client, test_module_wrapper_api, disconnection_type
    ):
        assert await client.get_connection_status() == "connected"

        logger.info("disconnecting network")
        await test_module_wrapper_api.network_disconnect(disconnection_type)

        logger.info("waiting for connection_status to change")
        await client.wait_for_connection_status_change()
        assert await client.get_connection_status() == "disconnected"

        logger.info("connection status has changed.  reconnecting")
        await test_module_wrapper_api.network_reconnect()

        logger.info("waiting for connection_status to change")
        await client.wait_for_connection_status_change()
        assert await client.get_connection_status() == "connected"

        logger.info("network is reconnected")
