#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import threading
import logging
import json
from swagger_server.models.connect_response import ConnectResponse
from azure.iot.hub.devicesdk import ModuleClient
from azure.iot.hub.devicesdk.auth.authentication_provider_factory import (
    from_connection_string,
    from_environment,
)

logging.basicConfig(level=logging.INFO)


class ModuleGlue:
    object_count = 1
    object_map = {}

    def _finish_connection(self, client):
        client.connect()

        connection_id = "moduleObject_" + str(self.object_count)
        self.object_count += 1
        self.object_map[connection_id] = client
        return ConnectResponse(connection_id)

    def connect_from_environment(self, transport_type):
        print("connecting from environment")
        auth_provider = from_environment()
        client = ModuleClient.from_authentication_provider(
            auth_provider, transport_type
        )
        return self._finish_connection(client)

    def connect(self, transport_type, connection_string, ca_certificate):
        print("connecting using " + transport_type)
        auth_provider = from_connection_string(connection_string)
        if "GatewayHostName" in connection_string:
            auth_provider.ca_cert = ca_certificate.cert
        client = ModuleClient.from_authentication_provider(
            auth_provider, transport_type
        )
        return self._finish_connection(client)

    def disconnect(self, connection_id):
        print("disconnecting " + connection_id)
        if connection_id in self.object_map:
            client = self.object_map[connection_id]
            client.disconnect()
            del self.object_map[connection_id]

    def enable_input_messages(self, connection_id):
        raise NotImplementedError()

    def enable_methods(self, connection_id):
        raise NotImplementedError()

    def enable_twin(self, connection_id):
        raise NotImplementedError()

    def send_event(self, connection_id, event_body):
        print("sending event on " + connection_id)
        client = self.object_map[connection_id]
        client.send_event(event_body.decode("utf-8"))
        print("send confirmation received")

    def wait_for_input_message(self, connection_id, input_name):
        raise NotImplementedError()

    def invoke_module_method(
        self, connection_id, device_id, module_id, method_invoke_parameters
    ):
        raise NotImplementedError()

    def invoke_device_method(self, connection_id, device_id, method_invoke_parameters):
        raise NotImplementedError()

    def roundtrip_method_call(self, connection_id, methodName, requestAndResponse):
        raise NotImplementedError()

    def send_output_event(self, connection_id, output_name, event_body):
        print("sending event on " + connection_id)
        client = self.object_map[connection_id]
        client.send_to_output(event_body.decode("utf-8"), output_name)
        print("send confirmation received")

    def wait_for_desired_property_patch(self, connection_id):
        raise NotImplementedError()

    def get_twin(self, connection_id):
        raise NotImplementedError()

    def send_twin_patch(self, connection_id, props):
        raise NotImplementedError()

    def cleanup_resources(self):
        listcopy = list(self.object_map.keys())
        for key in listcopy:
            print("object {} not cleaned up".format(key))
            self.disconnect(key)
