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
        return utilities.random_string()

    @pytest.fixture
    def invalid_correlation_id(self):
        return "Mjk5OTA0MjAyMjQ0X2YwMDE2ODJiLWMyOTItNGZiNi04MjUzLTZhZDQzZTI2ODIzMV9BRjRWU1BNNFNZQzJYWThGMFBSV09XS0VXUk9SOUFUUFJSSUVFVVZXU1Q4Vk1BMUUxWE84UjJUMFpVSVdCMVVVX3ZlcjIuMAo=="

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Fails updating status for invalid correlation id")
    async def test_blob_invalid_correlation_id(self, client, invalid_correlation_id):
        with pytest.raises(Exception):
            await client.notify_blob_upload_status(
                invalid_correlation_id, True, 200, "successful upload"
            )

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Can report a failed blob upload")
    async def test_failed_blob_upload(self, client, blob_name):
        info = await client.get_storage_info_for_blob(blob_name)

        assert info.additional_properties is not None
        assert info.blob_name == "{}/{}".format(client.device_id, blob_name)
        assert info.container_name
        assert info.correlation_id
        assert info.host_name
        assert info.sas_token

        await client.notify_blob_upload_status(
            info.correlation_id, False, 400, "failed upload"
        )
