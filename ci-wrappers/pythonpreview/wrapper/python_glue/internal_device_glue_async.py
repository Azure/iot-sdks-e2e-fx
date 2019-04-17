#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import auth
import json
import async_helper


def normalize_event_body(body):
    if isinstance(body, bytes):
        return body.decode("utf-8")
    else:
        return json.dumps(body)


def message_to_object(message):
    if isinstance(message.data, bytes):
        return message.data.decode("utf-8")
    else:
        return message.data


class InternalDeviceGlueAsync:
    def __init__(self):
        self.client = None
        # make sure we have an event loop
        async_helper.get_event_loop()

    def connect(self, transport_type, connection_string, cert):
        print("connecting using " + transport_type)
        auth_provider = auth.from_connection_string(connection_string)
        if "GatewayHostName" in connection_string:
            auth_provider.ca_cert = cert
        self.client = IoTHubDeviceClient.from_authentication_provider(
            auth_provider, transport_type
        )
        async_helper.run_coroutine_sync(self.client.connect())

    def disconnect(self):
        print("disconnecting")
        if self.client:
            async_helper.run_coroutine_sync(self.client.disconnect())
            self.client = None

    def enable_methods(self):
        pass

    def enable_twin(self):
        raise NotImplementedError()

    def enable_c2d(self):
        pass

    def send_event(self, event_body):
        print("sending event")
        async_helper.run_coroutine_sync(
            self.client.send_event(normalize_event_body(event_body))
        )
        print("send confirmation received")

    def wait_for_c2d_message(self):
        print("Waiting for c2d message")
        message = async_helper.run_coroutine_sync(self.client.receive_c2d_message())
        print("Message received")
        return message_to_object(message)

    def roundtrip_method_call(self, methodName, requestAndResponse):
        raise NotImplementedError()

    def wait_for_desired_property_patch(self):
        raise NotImplementedError()

    def get_twin(self):
        raise NotImplementedError()

    def send_twin_patch(self, props):
        raise NotImplementedError()
