# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import utilities
import json
from azure.storage.blob import BlobClient
import limitations
from horton_logging import logger

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


languages_that_support_blob_upload = set(["pythonv2"])


async def move_blob_status_into_eventhub(service, client):
    """
    get_blob_update_status() returns the status once, so we might receive status from
    a different instance of this test that's running in parallel.  we copy the update
    status into eventhub where it's available to any instance of this test.
    """
    while True:
        status = await service.get_blob_upload_status()
        logger("got upload status = {}".format(status))
        await client.send_event(json.loads(str(status)))


class BlobUploadTests(object):
    @pytest.fixture
    def blob_name(self):
        return utilities.random_string()

    @pytest.fixture
    def typical_blob_data(self):
        return utilities.next_random_string("typical_blob", length=257)

    @pytest.mark.it("Fails updating status for invalid correlation id")
    async def test_blob_invalid_correlation_id(self, client):
        limitations.only_run_test_for(client, languages_that_support_blob_upload)
        
        if limitations.needs_manual_connect(client):
            await client.connect2()
        with pytest.raises(Exception):
            await client.notify_blob_upload_status(
                invalid_correlation_id, True, success_code, success_message
            )

    @pytest.mark.it("Can report a failed blob upload")
    async def test_failed_blob_upload(self, client, blob_name):
        limitations.only_run_test_for(client, languages_that_support_blob_upload)

        if limitations.needs_manual_connect(client):
            await client.connect2()
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

    @pytest.mark.it("Fails to report success if nothing was uploaded")
    async def test_success_without_upload(self, client, blob_name):
        limitations.only_run_test_for(client, languages_that_support_blob_upload)

        if limitations.needs_manual_connect(client):
            await client.connect2()
        info = await client.get_storage_info_for_blob(blob_name)

        with pytest.raises(Exception):
            await client.notify_blob_upload_status(
                info.correlation_id, True, success_code, success_message
            )

        await client.notify_blob_upload_status(
            info.correlation_id, False, 400, "failed upload"
        )

    @pytest.mark.it("Can be used to successfully upload a blob")
    async def test_upload(
        self, client, service, eventhub, blob_name, typical_blob_data
    ):
        limitations.only_run_test_for(client, languages_that_support_blob_upload)

        if limitations.needs_manual_connect(client):
            await client.connect2()
        await eventhub.connect()

        await asyncio.sleep(5)

        move_future = asyncio.ensure_future(
            move_blob_status_into_eventhub(service, client)
        )

        try:
            info = await client.get_storage_info_for_blob(blob_name)

            blob_client = blob_client_from_info(info)

            blob_client.upload_blob(typical_blob_data)

            await client.notify_blob_upload_status(
                info.correlation_id, True, success_code, success_message
            )

            blob_data_copy = blob_client.download_blob().readall()

            assert blob_data_copy.decode() == typical_blob_data

            while True:
                upload_status = await eventhub.wait_for_next_event(device_id=None)
                if (
                    "blobName" in upload_status
                    and info.blob_name == upload_status["blobName"]
                ):
                    return
        finally:
            move_future.cancel()

            try:
                await move_future
            except asyncio.CancelledError:
                pass
