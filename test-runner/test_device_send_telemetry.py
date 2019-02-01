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

@pytest.mark.testgroup_iothub_module_client
@pytest.mark.callsSendEvent
@pytest.mark.module_under_test_has_device_wrapper
def test_device_send_event_to_iothub():

    log_message("connecting device client")
    device_client = connections.connect_leaf_device_client()
    log_message("connecting eventhub client")
    eventhub_client = connections.connect_eventhub_client()

    sent_message = test_utilities.random_string_in_json()
    log_message("sending event: " + str(sent_message))
    device_client.send_event(sent_message)

    log_message("wait for event to arrive at eventhub")
    received_message = eventhub_client.wait_for_next_event(
        environment.leaf_device_id,
        test_utilities.default_eventhub_timeout,
        expected=sent_message,
    )
    if not received_message:
        log_message("Message not received")
        assert False

    log_message("disconnecting device client")
    device_client.disconnect()
    log_message("disconnecting eventhub client")
    eventhub_client.disconnect()


@pytest.mark.asyncio
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.callsSendEvent
@pytest.mark.module_under_test_has_device_wrapper
async def test_device_send_event_to_iothub_async():

    executor = concurrent.futures.ThreadPoolExecutor()
    loop = asyncio.get_event_loop()

    log_message("connecting device client")
    device_client_async = await connections.connect_leaf_device_client_async()
    log_message("connecting eventhub client")
    eventhub_client = await loop.run_in_executor(executor, connections.connect_eventhub_client)

    sent_message = test_utilities.random_string_in_json()
    log_message("sending event: " + str(sent_message))
    await device_client_async.send_event(sent_message)

    log_message("wait for event to arrive at eventhub")
    received_message = await loop.run_in_executor(executor, eventhub_client.wait_for_next_event,
                               environment.leaf_device_id,
                               test_utilities.default_eventhub_timeout,
                               sent_message)
    if not received_message:
        log_message("Message not received")
        assert False

    log_message("disconnecting device client")
    await device_client_async.disconnect()
    log_message("disconnecting eventhub client")
    await loop.run_in_executor(executor, eventhub_client.disconnect)



