# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import time

receive_timeout = 60


class C2dTests(object):
    @pytest.mark.it("Can connect, enable C2D, and disconnect")
    async def test_client_connect_enable_c2d_disconnect(self, client):
        client.enable_c2d()

    @pytest.mark.it("Can receive C2D messages from the IoTHub Service")
    async def test_device_receive_c2d(self, client, service, test_string):
        client.enable_c2d()
        test_input_thread = client.wait_for_c2d_message_async()
        time.sleep(2)  # wait for receive pipeline to finish setting up

        service.send_c2d(client.device_id, test_string)

        received_message = test_input_thread.get(receive_timeout)
        assert received_message == test_string
