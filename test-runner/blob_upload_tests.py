# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
from horton_logging import logger


class BlobUploadTests(object):
    @pytest.mark.it("Can connect, enable twin, and disconnect")
    async def test_client_connect_enable_twin_disconnect(self, client):
        await client.enable_twin()

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Can get blob upload info")
    async def test_blob_upload(self, client):
        # BKTODO
        pass
