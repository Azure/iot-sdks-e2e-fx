# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import json
import asyncio
import limitations
from utilities import next_integer, next_random_string
from horton_logging import logger


async def run_method_call_test(source, destination):
    """
    Helper function which invokes a method call on one module and responds to it from another module
    """

    method_name = "test_method_{}".format(next_integer("test_method"))
    method_payload = {"payloadData": next_random_string("method_payload")}
    status_code = 1000 + next_integer("status_code")

    method_invoke_parameters = {
        "methodName": method_name,
        "payload": method_payload,
        "responseTimeoutInSeconds": 75,
        "connectTimeoutInSeconds": 60,
    }

    method_response_body = {"responseData": next_random_string("method_response")}

    if limitations.needs_manual_connect(destination):
        await destination.connect2()
    await destination.enable_methods()

    # start listening for method calls on the destination side
    receiver_future = asyncio.ensure_future(
        destination.wait_for_method_and_return_response(
            method_name, status_code, method_invoke_parameters, method_response_body
        )
    )

    if getattr(source, "methods_registered", False):
        registration_sleep = 0.5
    else:
        source.methods_registered = True
        registration_sleep = 10

    logger(
        "sleeping for {} seconds to make sure all registration is complete".format(
            registration_sleep
        )
    )
    await asyncio.sleep(registration_sleep)

    # invoking the call from caller side
    if getattr(destination, "module_id", None):
        sender_future = source.call_module_method(
            destination.device_id, destination.module_id, method_invoke_parameters
        )
    else:
        sender_future = source.call_device_method(
            destination.device_id, method_invoke_parameters
        )

    (response, _) = await asyncio.gather(sender_future, receiver_future)

    logger("method call complete.  Response is:")
    logger(str(response))

    # wait for that response to arrive back at the source and verify that it's all good.
    assert response["status"] == status_code
    # edge bug: the response that edge returns is stringified.  The same response that comes back from an iothub service call is not stringified
    if isinstance(response["payload"], str):
        response["payload"] = json.loads(response["payload"])
    assert response["payload"] == method_response_body

    await receiver_future


class BaseReceiveMethodCallTests(object):
    @pytest.mark.it("Can receive a method call from the IoTHub service")
    @pytest.mark.it("Can connect, enable methods, and disconnect")
    async def test_module_client_connect_enable_methods_disconnect(self, client):
        if limitations.needs_manual_connect():
            await client.connect2()
        await client.enable_methods()


class ReceiveMethodCallFromServiceTests(BaseReceiveMethodCallTests):
    @pytest.mark.it("Can receive a method call from the IoTHub service")
    async def test_method_call_invoked_from_service(self, client, service):
        await run_method_call_test(source=service, destination=client)


class ReceiveMethodCallFromModuleTests(BaseReceiveMethodCallTests):
    @pytest.mark.it("Can receive a method call from an EdgeHub module")
    async def test_method_call_invoked_from_friend(self, client, friend):
        await run_method_call_test(source=friend, destination=client)


class InvokeMethodCallOnModuleTests(object):
    @pytest.mark.it("Can invoke a method call on an EdgeHub module")
    async def test_method_call_invoked_on_friend(self, client, friend):
        if limitations.uses_shared_key_auth(client):
            limitations.skip_test_for(client, ["pythonv2", "c"])

        await run_method_call_test(source=client, destination=friend)


class InvokeMethodCallOnLeafDeviceTests(object):
    @pytest.mark.it("Can invoke a method call on an EdgeHub leaf device")
    async def test_method_call_invoked_on_leaf_device(self, client, leaf_device):
        if limitations.uses_shared_key_auth(client):
            limitations.skip_test_for(client, ["pythonv2", "c"])

        await run_method_call_test(source=client, destination=leaf_device)
