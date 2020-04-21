# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import utilities
from horton_logging import logger
from azure.storage.blob import BlobClient

invalid_correlation_id = "Mjk5OTA0MjAyMjQ0X2YwMDE2ODJiLWMyOTItNGZiNi04MjUzLTZhZDQzZTI2ODIzMV9BRjRWU1BNNFNZQzJYWThGMFBSV09XS0VXUk9SOUFUUFJSSUVFVVZXU1Q4Vk1BMUUxWE84UjJUMFpVSVdCMVVVX3ZlcjIuMAo=="
success_code = 200
success_message = "successful upload"
failure_code = 400
failure_message = "failed upload"


def blob_client_from_info(info):
    sas_url = "https://{}/{}/{}{}".format(
        info.host_name, info.container_name, info.blob_name, info.sas_token
    )
    return BlobClient.from_blob_url(sas_url)


class BlobUploadTests(object):
    @pytest.fixture
    def blob_name(self):
        return utilities.random_string()

    @pytest.fixture
    def typical_blob_data(self):
        return utilities.next_random_string("typical_blob", length=257)

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Fails updating status for invalid correlation id")
    async def test_blob_invalid_correlation_id(self, client):
        with pytest.raises(Exception):
            await client.notify_blob_upload_status(
                invalid_correlation_id, True, success_code, success_message
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
            info.correlation_id, False, failure_code, failure_message
        )

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Fails to report success if noting was uploaded")
    async def test_success_without_upload(self, client, blob_name):
        info = await client.get_storage_info_for_blob(blob_name)

        with pytest.raises(Exception):
            await client.notify_blob_upload_status(
                info.correlation_id, True, success_code, success_message
            )

        await client.notify_blob_upload_status(
            info.correlation_id, False, 400, "failed upload"
        )

    @pytest.mark.supports_blob_upload
    @pytest.mark.it("Can be used to successfully upload a blob")
    async def test_upload(self, client, blob_name, typical_blob_data):
        info = await client.get_storage_info_for_blob(blob_name)

        blob_client = blob_client_from_info(info)

        blob_client.upload_blob(typical_blob_data)

        await client.notify_blob_upload_status(
            info.correlation_id, True, success_code, success_message
        )
