# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import time
import test_utilities
from runtime_config import get_current_config
from adapters import print_message as log_message

receive_timeout = 60


@pytest.mark.testgroup_iothub_device_client
def test_device_receive_c2d(test_string):
    device_client = None
    service = None

    try:
        device_client = connections.connect_test_device_client()
        service = connections.connect_service_client()

        device_client.enable_c2d()
        test_input_thread = device_client.wait_for_c2d_message_async()
        time.sleep(2)  # wait for receive pipeline to finish setting up

        service.send_c2d(get_current_config().test_device.device_id, test_string)

        received_message = test_input_thread.get(receive_timeout)
        assert received_message == test_string
    finally:
        if device_client:
            device_client.disconnect()
        if service:
            service.disconnect()
