#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import test_utilities
import environment
from adapters import print_message as log_message
import concurrent
import asyncio
import time


@pytest.mark.testgroup_iothub_module_client
@pytest.mark.callsSendEvent
def test_device_receive_c2d_from_iothub():

    # sent_message = test_utilities.random_string_in_json()
    # log_message("sending event: " + str(sent_message))

    log_message("connecting device client")
    device_client = connections.connect_leaf_device_client()

    expected_message = "Mimbulus Mimbletonia"
    service = connections.connect_service_client()
    service.send_c2d(environment.leaf_device_id, expected_message)
    service.disconnect()

    log_message("wait for event to arrive at device client ")
    c2d_message_queue = device_client.receive_c2d()
    received_c2d_message = wait_for_c2d_message(c2d_message_queue, 40, environment.leaf_device_id, expected_message)

    if not received_c2d_message:
        log_message("Message not received")
        assert False

    log_message("disconnecting device client")
    device_client.disconnect()


def wait_for_c2d_message(c2d_message_queue, timeout, device_id, expected=None):
    log_message("DeviceAPI: waiting for c2d at {}".format(device_id))
    start_time = time.time()
    received_c2d_message = c2d_message_queue.get()  # blocking cal
    return received_c2d_message
    # while (time.time() - start_time) < timeout:
    #     received_c2d_message = c2d_message_queue.get()  # blocking call
    #     log_message("The message received was " + received_c2d_message)
    #     if expected == received_c2d_message:
    #         log_message("DeviceAPI: message received as expected")
    #         return received_c2d_message
    #     else:
    #         log_message("DeviceAPI: unexpected message.  skipping")
    # return received_c2d_message
