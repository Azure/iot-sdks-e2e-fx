# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.models.connect_response import ConnectResponse
from internal_module_glue import InternalModuleGlue
import json


class ModuleGlue:
    object_count = 1
    object_map = {}

    def _return_connect_response(self, internal):
        connection_id = "moduleObject_" + str(self.object_count)
        self.object_count += 1
        self.object_map[connection_id] = internal
        return ConnectResponse(connection_id)

    def connect_from_environment_v1(self, transport_type):
        internal = InternalModuleGlue()
        internal.connect_from_environment_v1(transport_type)
        return self._return_connect_response(internal)

    def connect_v1(self, transport_type, connection_string, ca_certificate):
        internal = InternalModuleGlue()
        internal.connect_v1(transport_type, connection_string, ca_certificate.cert)
        return self._return_connect_response(internal)

    def disconnect(self, connection_id):
        print("disconnecting " + connection_id)
        if connection_id in self.object_map:
            internal = self.object_map[connection_id]
            internal.disconnect()
            del self.object_map[connection_id]

    def enable_input_messages(self, connection_id):
        self.object_map[connection_id].enable_input_messages()

    def enable_methods(self, connection_id):
        self.object_map[connection_id].enable_methods()

    def enable_twin(self, connection_id):
        self.object_map[connection_id].enable_twin()

    def send_event(self, connection_id, event_body):
        self.object_map[connection_id].send_event(event_body)

    def wait_for_input_message(self, connection_id, input_name):
        response = self.object_map[connection_id].wait_for_input_message(input_name)
        return json.dumps(response)

    def invoke_module_method(
        self, connection_id, device_id, module_id, method_invoke_parameters
    ):
        self.object_map[connection_id].invoke_module_method(
            device_id, module_id, method_invoke_parameters
        )

    def invoke_device_method(self, connection_id, device_id, method_invoke_parameters):
        self.object_map[connection_id].invoke_device_method(
            device_id, method_invoke_parameters
        )

    def roundtrip_method_call(self, connection_id, method_name, request_and_response):
        self.object_map[connection_id].roundtrip_method_call(
            method_name, request_and_response
        )

    def send_output_event(self, connection_id, output_name, event_body):
        self.object_map[connection_id].send_output_event(output_name, event_body)

    def wait_for_desired_property_patch(self, connection_id):
        return self.object_map[connection_id].wait_for_desired_property_patch()

    def get_twin(self, connection_id):
        return self.object_map[connection_id].get_twin()

    def send_twin_patch(self, connection_id, props):
        self.object_map[connection_id].send_twin_patch(props)

    def get_connection_status(self, connection_id):
        self.object_map[connection_id].get_connection_status()

    def wait_for_connection_status_change(self, connection_id):
        self.object_map[connection_id].wait_for_connection_status_change()

    def cleanup_resources(self):
        listcopy = list(self.object_map.keys())
        for key in listcopy:
            print("object {} not cleaned up".format(key))
            self.disconnect(key)
