#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import auth, MethodResponse
from threading import Event
import json
import async_helper


def normalize_event_body(body):
    if isinstance(body, bytes):
        return body.decode("utf-8")
    else:
        return json.dumps(body)


def message_to_object(message):
    return json.loads(message.data.decode("utf-8"))


class InternalModuleGlueAsync:
    def __init__(self):
        self.client = None
        # make sure we have an event loop
        async_helper.get_event_loop()

    def connect_from_environment(self, transport_type):
        print("connecting from environment")
        auth_provider = auth.from_environment()
        self.client = IoTHubModuleClient.from_authentication_provider(
            auth_provider, transport_type
        )
        async_helper.run_coroutine_sync(self.client.connect())

    def connect(self, transport_type, connection_string, cert):
        print("connecting using " + transport_type)
        auth_provider = auth.from_connection_string(connection_string)
        if "GatewayHostName" in connection_string:
            auth_provider.ca_cert = cert
        self.client = IoTHubModuleClient.from_authentication_provider(
            auth_provider, transport_type
        )
        async_helper.run_coroutine_sync(self.client.connect())

    def disconnect(self):
        print("disconnecting")
        if self.client:
            async_helper.run_coroutine_sync(self.client.disconnect())
            self.client = None

    def enable_input_messages(self):
        # Unnecessary, input messages are enabled implicitly when input operations are initiated.
        pass

    def enable_methods(self):
        # Unnecessary, methods are enabled implicity when method operations are initiated.
        pass

    def enable_twin(self):
        raise NotImplementedError()

    def send_event(self, event_body):
        print("sending event")
        async_helper.run_coroutine_sync(
            self.client.send_event(normalize_event_body(event_body))
        )
        print("send confirmation received")

    def wait_for_input_message(self, input_name):
        print("Waiting for input message")
        message = async_helper.run_coroutine_sync(
            self.client.receive_input_message(input_name)
        )
        print("Message received")
        return message_to_object(message)

    def invoke_module_method(self, device_id, module_id, method_invoke_parameters):
        raise NotImplementedError()

    def invoke_device_method(self, device_id, method_invoke_parameters):
        raise NotImplementedError()

    def roundtrip_method_call(self, methodName, requestAndResponse):
       # receive method request
        print("Waiting for method request")
        request = async_helper.run_coroutine_sync(self.client.receive_method_request(methodName))
        print("Method request received")

        # verify name and payload
        expected_name = methodName
        expected_payload = requestAndResponse.request_payload['payload']
        if (request.name == expected_name):
            if (request.payload == expected_payload):
                print("Method name and payload matched. Returning response")
                resp_status = requestAndResponse.status_code
                resp_payload = requestAndResponse.response_payload
            else:
                print("Request payload doesn't match")
                print("expected: " + expected_payload)
                print("received: " + request.payload)
                resp_status = 500
                resp_payload = None
        else:
            print("Method name doesn't match")
            print("expected: '" + expected_name + "'")
            print("received: '" + request.name + "'")
            resp_status = 404
            resp_payload = None

        # send method response
        response = MethodResponse(request_id=request.request_id, status=resp_status, payload=resp_payload)
        async_helper.run_coroutine_sync(self.client.send_method_response(response))
        print("Method response sent")

    def send_output_event(self, output_name, event_body):
        print("sending output event")
        async_helper.run_coroutine_sync(
            self.client.send_to_output(normalize_event_body(event_body), output_name)
        )
        print("send confirmation received")

    def wait_for_desired_property_patch(self):
        raise NotImplementedError()

    def get_twin(self):
        raise NotImplementedError()

    def send_twin_patch(self, props):
        raise NotImplementedError()
