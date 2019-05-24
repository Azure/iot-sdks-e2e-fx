#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import json
import multiprocessing
import time
from adapters import print_message as log_message
from runtime_config import get_current_config

# How long do we have to wait after a module registers to receive
# method calls until we can actually call a method.
time_for_method_to_fully_register = 5
# when we're invoking from the service, we give it more time
time_for_method_to_fully_register_service_call = 15

method_name = "test_method"
method_payload = '"Look at me, I\'ve got payload!"'
status_code = 221

method_invoke_parameters = {
    "methodName": method_name,
    "payload": method_payload,
    "responseTimeoutInSeconds": 75,
    "connectTimeoutInSeconds": 60,
}

method_response_body = {"response": "Look at me.  I'm a response!"}


def do_module_method_call(
    source_module,
    destination_module,
    destination_device_id,
    destination_module_id,
    registration_sleep=time_for_method_to_fully_register,
):
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
    log_message(
        "sleeping for {} seconds to make sure all registration is complete".format(
            registration_sleep
        )
    )
    time.sleep(registration_sleep)

    # invoking the call from caller side
    log_message("invoking method call")
    response = source_module.call_module_method_async(
        destination_device_id, destination_module_id, method_invoke_parameters
    ).get()
    log_message("method call complete.  Response is:")
    log_message(str(response))

    # wait for that response to arrive back at the source and verify that it's all good.
    assert response["status"] == status_code
    # edge bug: the response that edge returns is stringified.  The same response that comes back from an iothub service call is not stringified
    if isinstance(response["payload"], str):
        response["payload"] = json.loads(response["payload"])
    assert response["payload"] == method_response_body

    receiver_thread.wait()


@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.receivesMethodCalls
def test_module_method_call_invoked_from_service():
    """
    invoke a module call from the service and responds to it from the test module.
    """

    service_client = connections.connect_service_client()
    module_client = connections.connect_test_module_client()

    do_module_method_call(
        service_client,
        module_client,
        get_current_config().test_module.device_id,
        get_current_config().test_module.module_id,
        registration_sleep=time_for_method_to_fully_register_service_call,
    )

    module_client.disconnect()
    service_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.receivesMethodCalls
def test_module_method_from_friend_to_test():
    """
    invoke a method call from the friend module and respond to it from the test module
    """

    module_client = connections.connect_test_module_client()
    friend_client = connections.connect_friend_module_client()

    do_module_method_call(
        friend_client,
        module_client,
        get_current_config().test_module.device_id,
        get_current_config().test_module.module_id,
    )

    module_client.disconnect()
    friend_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.invokesModuleMethodCalls
def test_module_method_from_test_to_friend():
    """
    invoke a method call from the test module and respond to it from the friend module
    """

    module_client = connections.connect_test_module_client()
    friend_client = connections.connect_friend_module_client()

    do_module_method_call(
        module_client,
        friend_client,
        get_current_config().friend_module.device_id,
        get_current_config().friend_module.module_id,
    )

    module_client.disconnect()
    friend_client.disconnect()
