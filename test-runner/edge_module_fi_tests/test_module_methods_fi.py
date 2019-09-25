# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import json
import multiprocessing
import time
from adapters import print_message
from edgehub_control import disconnect_edgehub, connect_edgehub, restart_edgehub
from runtime_config import get_current_config
import docker


client = docker.from_env()


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
    print_message("enabling methods on the destination")
    destination_module.enable_methods()

    # start listening for method calls on the destination side
    print_message("starting to listen from destination module")
    receiver_thread = destination_module.roundtrip_method_async(
        method_name, status_code, method_invoke_parameters, method_response_body
    )
    print_message(
        "sleeping for {} seconds to make sure all registration is complete".format(
            registration_sleep
        )
    )
    time.sleep(registration_sleep)

    disconnect_edgehub()  # One point that could be good to disconnect edgeHub
    # time.sleep(1)
    connect_edgehub()
    print_message("Sleeping")
    time.sleep(30)
    print_message(" Done Sleeping")

    # invoking the call from caller side
    print_message("invoking method call")
    response = source_module.call_module_method_async(
        destination_device_id, destination_module_id, method_invoke_parameters
    ).get()
    print_message("method call complete.  Response is:")
    print_message(str(response))

    # wait for that response to arrive back at the source and verify that it's all good.
    assert response["status"] == status_code
    # edge bug: the response that edge returns is stringified.  The same response that comes back from an iothub service call is not stringified
    if isinstance(response["payload"], str):
        response["payload"] = json.loads(response["payload"])
    assert response["payload"] == method_response_body

    receiver_thread.wait()


@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.receivesMethodCalls
def test_module_method_call_invoked_from_service():
    """
    invoke a module call from the service and responds to it from the test module.
    """

    restart_edgehub(hard=True)
    time.sleep(5)
    service_client = connections.connect_service_client()
    module_client = connections.connect_test_module_client()
    do_module_method_call(
        service_client,
        module_client,
        get_current_config().test_module.device_id,
        get_current_config().test_module.module_id,
        registration_sleep=time_for_method_to_fully_register_service_call,
    )

    module_client.disconnect_sync()
    service_client.disconnect_sync()


@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.invokesModuleMethodCalls
def test_module_method_from_test_to_friend_fi():
    """
  invoke a method call from the test module and respond to it from the friend module
  """

    module_client = connections.connect_test_module_client()
    friend_client = connections.connect_friend_module_client()
    time.sleep(5)
    do_module_method_call(
        module_client,
        friend_client,
        get_current_config().friend_module.device_id,
        get_current_config().friend_module.module_id,
    )

    module_client.disconnect_sync()
    friend_client.disconnect_sync()


@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.receivesMethodCalls
@pytest.mark.invokesModuleMethodCalls
def test_module_method_from_friend_to_test_fi():
    """
  invoke a method call from the friend module and respond to it from the test module
  """

    module_client = connections.connect_test_module_client()
    friend_client = connections.connect_friend_module_client()
    time.sleep(5)
    do_module_method_call(
        friend_client,
        module_client,
        get_current_config().test_module.device_id,
        get_current_config().test_module.module_id,
    )

    module_client.disconnect_sync()
    friend_client.disconnect_sync()
