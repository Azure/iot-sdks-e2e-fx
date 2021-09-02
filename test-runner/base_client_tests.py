# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest


class BaseClientTests(object):
    @pytest.mark.skip(reason="")
    @pytest.mark.it("Can connect and immediately disconnect")
    async def test_client_connect_disconnect(self, client):
        await client.connect2()
