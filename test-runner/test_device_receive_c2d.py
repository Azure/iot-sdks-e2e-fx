#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import environment
from adapters import print_message as log_message
import time
import threading


@pytest.mark.testgroup_iothub_module_client
@pytest.mark.callsSendEvent
def test_device_receive_c2d_from_iothub_single():

    log_message("connecting device client")
    device_client = connections.connect_leaf_device_client()
    expected_message = "This is an end to end message"

    log_message("wait for event to arrive at device client ")
    c2d_message_queue = device_client.receive_c2d()

    expected_messages = [None] * 1
    expected_messages[0] = expected_message
    service = connections.connect_service_client()
    service.send_c2d(environment.leaf_device_id, expected_message)
    service.disconnect()

    result_messages = [None] * 1
    listen_thread = threading.Thread(target=wait_for_c2d_message, args=(c2d_message_queue, 5, environment.leaf_device_id, result_messages, expected_messages, 0, 1))
    listen_thread.daemon = True
    listen_thread.start()

    print("This may print while the thread is running.")
    listen_thread.join(10)
    print("This will always print after the thread has finished.")

    result_message = result_messages[0]
    if not result_message:
        log_message("Message not received")
        assert False

    log_message("disconnecting device client")
    device_client.disconnect()


@pytest.mark.testgroup_iothub_module_client
@pytest.mark.callsSendEvent
def test_device_receive_c2d_from_iothub_multiple():

    number_of_messages = 3
    log_message("connecting device client")
    device_client = connections.connect_leaf_device_client()
    expected_message = "This is an end to end message numbered"
    expected_messages = [None] * number_of_messages

    log_message("wait for event to arrive at device client ")
    c2d_message_queue = device_client.receive_c2d()

    for i in range(0, number_of_messages):
        # We have to connect service client in a new instance always as we get following error
        # ValueError: The supplied authentication has already been consumed by another connection.
        # Please create a fresh instance.
        service = connections.connect_service_client()
        expected_messages[i] = expected_message + " i"
        time.sleep(2)
        service.send_c2d(environment.leaf_device_id, expected_messages[i])
        service.disconnect()

    result_messages = [None] * number_of_messages
    listen_thread = threading.Thread(target=wait_for_c2d_message, args=(c2d_message_queue, 10, environment.leaf_device_id, result_messages, expected_messages, 0, number_of_messages))
    listen_thread.daemon = True
    listen_thread.start()

    print("This may print while the thread is running.")
    listen_thread.join(20)
    print("This will always print after the thread has finished.")

    for i in range(0, number_of_messages):
        result_message = result_messages[i]
        if not result_message:
            log_message("Message not received")
            assert False

    log_message("disconnecting device client")
    device_client.disconnect()


def wait_for_c2d_message(c2d_message_queue, timeout, device_id, results, expected, index, capacity):
    log_message("DeviceAPI: waiting for c2d at {}".format(device_id))
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        received_c2d_message = c2d_message_queue.get()
        actual = str(received_c2d_message.data, "utf-8")
        log_message("The message received was " + actual)
        if expected[index] == actual:
            log_message("DeviceAPI: message received as expected")
            results[index] = actual
            if index == capacity:
                return
            index = index + 1
        else:
            log_message("DeviceAPI: unexpected message.  skipping")
