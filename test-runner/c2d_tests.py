# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio


class C2dTests(object):
    @pytest.mark.it("Can connect, enable C2D, and disconnect")
    async def test_client_connect_enable_c2d_disconnect(self, client):
        await client.enable_c2d()

    @pytest.mark.it("Can receive C2D messages from the IoTHub Service")
    async def test_device_receive_c2d(self, client, service, test_string):
        await client.enable_c2d()
        test_input_future = asyncio.ensure_future(client.wait_for_c2d_message())
        await asyncio.sleep(2)  # wait for receive pipeline to finish setting up

        await service.send_c2d(client.device_id, test_string)

        received_message = await test_input_future
        assert received_message == test_string
