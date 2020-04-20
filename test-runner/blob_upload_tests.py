# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import utilities
from horton_logging import logger


class BlobUploadTests(object):
    @pytest.fixture
    def blob_name(self):
        return utilities.next_random_string("blob")

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Can get blob upload info")
    async def test_blob_upload(self, client, blob_name):
        info = await client.get_storage_info_for_blob(blob_name)
        assert info.additional_properties is not None
        assert info.blob_name == "{}/{}".format(client.device_id, blob_name)
        assert info.container_name
        assert info.correlation_id
        assert info.host_name
        assert info.sas_token
