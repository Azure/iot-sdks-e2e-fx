# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import json
import multiprocessing
import time

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


def run_method_call_test(
    logger, source, destination, registration_sleep=time_for_method_to_fully_register
):
    """
    Helper function which invokes a method call on one module and responds to it from another module
    """
    destination.enable_methods()

    # start listening for method calls on the destination side
    receiver_thread = destination.roundtrip_method_async(
        method_name, status_code, method_invoke_parameters, method_response_body
    )
    logger(
        "sleeping for {} seconds to make sure all registration is complete".format(
            registration_sleep
        )
    )
    time.sleep(registration_sleep)

    # invoking the call from caller side
    if getattr(destination, "module_id", None):
        response = source.call_module_method_async(
            destination.device_id, destination.module_id, method_invoke_parameters
        ).get()
    else:
        response = source.call_device_method_async(
            destination.device_id, method_invoke_parameters
        ).get()

    logger("method call complete.  Response is:")
    logger(str(response))

    # wait for that response to arrive back at the source and verify that it's all good.
    assert response["status"] == status_code
    # edge bug: the response that edge returns is stringified.  The same response that comes back from an iothub service call is not stringified
    if isinstance(response["payload"], str):
        response["payload"] = json.loads(response["payload"])
    assert response["payload"] == method_response_body

    receiver_thread.wait()


class BaseReceiveMethodCallTests(object):
    @pytest.mark.receivesMethodCalls
    @pytest.mark.it("Can receive a method call from the IoTHub service")
    @pytest.mark.it("Can connect, enable methods, and disconnect")
    def test_module_client_connect_enable_methods_disconnect(self, client):
        client.enable_methods()


# BKTODO remove marks like receivesMethodCalls
class ReceiveMethodCallFromServiceTests(BaseReceiveMethodCallTests):
    @pytest.mark.timeout(180)
    @pytest.mark.receivesMethodCalls
    @pytest.mark.it("Can receive a method call from the IoTHub service")
    def test_method_call_invoked_from_service(self, client, service, logger):
        run_method_call_test(
            source=service,
            destination=client,
            logger=logger,
            registration_sleep=time_for_method_to_fully_register_service_call,
        )


class ReceiveMethodCallFromModuleTests(BaseReceiveMethodCallTests):
    @pytest.mark.timeout(180)
    @pytest.mark.receivesMethodCalls
    @pytest.mark.it("Can receive a method call from an EdgeHub module")
    def test_method_call_invoked_from_friend(self, client, friend, logger):
        run_method_call_test(source=friend, destination=client, logger=logger)


class InvokeMethodCallOnModuleTests(object):
    @pytest.mark.timeout(180)
    @pytest.mark.invokesModuleMethodCalls
    @pytest.mark.it("Can invoke a method call on an EdgeHub module")
    def test_method_call_invoked_on_friend(self, client, friend, logger):
        run_method_call_test(source=client, destination=friend, logger=logger)


class InvokeMethodCallOnLeafDeviceTests(object):
    @pytest.mark.timeout(180)
    @pytest.mark.invokesDeviceMethodCalls
    @pytest.mark.it("Can invoke a method call on an EdgeHub leaf device")
    def test_method_call_invoked_on_leaf_device(self, client, leaf_device, logger):
        run_method_call_test(source=client, destination=leaf_device, logger=logger)
