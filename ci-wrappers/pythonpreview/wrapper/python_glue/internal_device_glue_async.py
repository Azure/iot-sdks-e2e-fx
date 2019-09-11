#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import MethodResponse
import json
import async_helper
import convert


class InternalDeviceGlueAsync:
    def __init__(self):
        self.client = None
        # make sure we have an event loop
        async_helper.get_event_loop()

    def connect(self, transport_type, connection_string, cert):
        print("connecting using " + transport_type)
        if "GatewayHostName" in connection_string:
            self.client = IoTHubDeviceClient.create_from_connection_string(
                connection_string, ca_cert=cert
            )
        else:
            self.client = IoTHubDeviceClient.create_from_connection_string(
                connection_string
            )
        async_helper.run_coroutine_sync(self.client.connect())

    def disconnect(self):
        print("disconnecting")
        if self.client:
            async_helper.run_coroutine_sync(self.client.disconnect())
            self.client = None

    def enable_methods(self):
        # Unnecessary, methods are enabled implicity when method operations are initiated.
        pass

    def enable_twin(self):
        pass

    def enable_c2d(self):
        # Unnecessary, C2D messages are enabled implicitly when C2D operations are initiated.
        pass

    def send_event(self, event_body):
        print("sending event")
        async_helper.run_coroutine_sync(
            self.client.send_message(
                convert.test_script_object_to_outgoing_message(event_body)
            )
        )
        print("send confirmation received")

    def wait_for_c2d_message(self):
        print("Waiting for c2d message")
        message = async_helper.run_coroutine_sync(self.client.receive_message())
        print("Message received")
        return convert.incoming_message_to_test_script_object(message)

    def roundtrip_method_call(self, methodName, requestAndResponse):
        # receive method request
        print("Waiting for method request")
        request = async_helper.run_coroutine_sync(
            self.client.receive_method_request(methodName)
        )
        print("Method request received")

        # verify name and payload
        expected_name = methodName
        expected_payload = requestAndResponse.request_payload["payload"]
        if request.name == expected_name:
            if request.payload == expected_payload:
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
        response = MethodResponse(
            request_id=request.request_id, status=resp_status, payload=resp_payload
        )
        async_helper.run_coroutine_sync(self.client.send_method_response(response))
        print("Method response sent")

    def wait_for_desired_property_patch(self):
        print("Waiting for desired property patch")
        patch = async_helper.run_coroutine_sync(
            self.client.receive_twin_desired_properties_patch()
        )
        print("patch received")
        return patch

    def get_twin(self):
        print("getting twin")
        twin = async_helper.run_coroutine_sync(self.client.get_twin())
        print("done getting twin")
        return {"properties": twin}

    def send_twin_patch(self, props):
        print("setting reported property patch")
        async_helper.run_coroutine_sync(
            self.client.patch_twin_reported_properties(props)
        )
        print("done setting reported properties")
