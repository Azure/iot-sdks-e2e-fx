#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import json
import time
from adapters import print_message as log_message
from runtime_config import get_current_config

# How long do we have to wait after a module registers to receive
# method calls until we can actually call a method.
time_for_method_to_fully_register = 5

method_name = "test_method"
method_payload = '"Look at me, I\'ve got payload!"'
status_code = 221

method_invoke_parameters = {
    "methodName": method_name,
    "payload": method_payload,
    "responseTimeoutInSeconds": 15,
    "connectTimeoutInSeconds": 15,
}

method_response_body = {"response": "Look at me.  I'm a response!"}


def do_device_method_call(source_module, destination_module, destination_device_id):
    """
    Helper function which invokes a method call on one module and responds to it from another module
    """
    log_message("enabling methods on the destination")
    destination_module.enable_methods()

    # start listening for method calls on the destination side
    log_message("starting to listen from destination module")
    receiver_thread = destination_module.roundtrip_method_async(
        method_name, status_code, method_invoke_parameters, method_response_body
    )
    time.sleep(time_for_method_to_fully_register)

    # invoking the call from caller side
    log_message("invoking method call")
    response = source_module.call_device_method_async(
        destination_device_id, method_invoke_parameters
    ).get()
    log_message("method call complete.  Response is:")
    log_message(str(response))

    # wait for that response to arrive back at the source and verify that it's all good.
    log_message("response = " + str(response) + "\n")
    assert response["status"] == status_code
    # edge bug: the response that edge returns is stringified.  The same response that comes back from an iothub service call is not stringified
    if isinstance(response["payload"], str):
        response["payload"] = json.loads(response["payload"])
    assert response["payload"] == method_response_body

    receiver_thread.wait()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.module_under_test_has_device_wrapper
def test_device_method_from_service_to_leaf_device():
    """
    invoke a method call from the service API and respond to it from the leaf device
    """

    service_client = connections.connect_service_client()
    leaf_device_client = connections.connect_leaf_device_client()

    do_device_method_call(
        service_client, leaf_device_client, get_current_config().leaf_device.device_id
    )

    service_client.disconnect()
    leaf_device_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.invokesDeviceMethodCalls
def test_device_method_from_module_to_leaf_device():
    """
    invoke a method call from the test module and respond to it from the leaf device
    """

    module_client = connections.connect_test_module_client()
    leaf_device_client = connections.connect_leaf_device_client()

    do_device_method_call(
        module_client, leaf_device_client, get_current_config().leaf_device.device_id
    )

    module_client.disconnect()
    leaf_device_client.disconnect()
