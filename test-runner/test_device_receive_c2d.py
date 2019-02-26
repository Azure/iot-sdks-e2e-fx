#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import test_utilities
import environment
from adapters import print_message as log_message
import time
import threading


@pytest.mark.testgroup_iothub_module_client
@pytest.mark.callsSendEvent
def test_device_receive_c2d_from_iothub():

    # sent_message = test_utilities.random_string_in_json()
    # log_message("sending event: " + str(sent_message))

    log_message("connecting device client")
    device_client = connections.connect_leaf_device_client()
    expected_message = "Mimbulus Mimbletonia"

    log_message("wait for event to arrive at device client ")
    c2d_message_queue = device_client.receive_c2d()

    service = connections.connect_service_client()
    service.send_c2d(environment.leaf_device_id, expected_message)
    service.disconnect()

    time.sleep(2)

    result_message = c2d_message_queue.get()
    if not result_message:
        log_message("Message not received")
        assert False

    log_message("disconnecting device client")
    device_client.disconnect()


def wait_for_c2d_message(c2d_message_queue, timeout, device_id, result_message=None, expected=None):
    log_message("DeviceAPI: waiting for c2d at {}".format(device_id))
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        received_c2d_message = c2d_message_queue.get()
        actual = str(received_c2d_message.data, "utf-8")
        log_message("The message received was " + actual)
        if expected == actual:
            log_message("DeviceAPI: message received as expected")
            result_message = actual
        else:
            log_message("DeviceAPI: unexpected message.  skipping")
    return result_message
