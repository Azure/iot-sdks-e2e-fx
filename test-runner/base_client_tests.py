# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import logging

logger = logging.getLogger(__name__)


class BaseClientTests(object):
    @pytest.mark.it("Can connect and immediately disconnect")
    async def test_client_connect_disconnect(self, client):
        if client.capabilities.v2_connect_group:
            await client.connect2()
