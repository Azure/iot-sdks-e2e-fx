# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.models.connect_response import ConnectResponse
from internal_device_glue import InternalDeviceGlue
import json


class DeviceGlue:
    object_count = 1
    object_map = {}

    def _finish_connection(self, internal):
        connection_id = "deviceObject_" + str(self.object_count)
        self.object_count += 1
        self.object_map[connection_id] = internal
        return ConnectResponse(connection_id)

    def connect(self, transport_type, connection_string, ca_certificate):
        internal = InternalDeviceGlue()
        internal.connect(transport_type, connection_string, ca_certificate.cert)
        return self._finish_connection(internal)

    def disconnect(self, connection_id):
        print("disconnecting " + connection_id)
        if connection_id in self.object_map:
            internal = self.object_map[connection_id]
            internal.disconnect()
            del self.object_map[connection_id]

    def enable_methods(self, connection_id):
        self.object_map[connection_id].enable_methods()

    def enable_c2d(self, connection_id):
        self.object_map[connection_id].enable_c2d()

    def send_event(self, connection_id, event_body):
        self.object_map[connection_id].send_event(event_body)

    def wait_for_c2d_message(self, connection_id):
        response = self.object_map[connection_id].wait_for_c2d_message()
        return json.dumps(response)

    def roundtrip_method_call(self, connection_id, method_name, request_and_response):
        self.object_map[connection_id].roundtrip_method_call(
            method_name, request_and_response
        )

    def wait_for_desired_property_patch(self, connection_id):
        return self.object_map[connection_id].wait_for_desired_property_patch()

    def enable_twin(self, connection_id):
        self.object_map[connection_id].enable_twin()

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
