# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.models.connect_response import ConnectResponse
from swagger_server.models.event_body import EventBody
from internal_glue_factory import create_glue_object
import json
import logging

logger = logging.getLogger(__name__)


class ModuleGlue:
    object_count = 1
    object_map = {}

    def _return_connect_response(self, internal):
        connection_id = "moduleObject_" + str(self.object_count)
        self.object_count += 1
        self.object_map[connection_id] = internal
        return ConnectResponse(connection_id)

    def connect_from_environment_sync(self, transport_type):
        internal = create_glue_object("module", "sync_interface")
        internal.connect_from_environment_sync(transport_type)
        return self._return_connect_response(internal)

    def connect_sync(self, transport_type, connection_string, ca_certificate):
        internal = create_glue_object("module", "sync_interface")
        internal.connect_sync(transport_type, connection_string, ca_certificate.cert)
        return self._return_connect_response(internal)

    def disconnect_sync(self, connection_id):
        logger.info("disconnecting " + connection_id)
        if connection_id in self.object_map:
            internal = self.object_map[connection_id]
            internal.disconnect_sync()
            del self.object_map[connection_id]

    def create_from_connection_string_sync(
        self, transport_type, connection_string, ca_certificate
    ):
        internal = create_glue_object("module", "sync_interface")
        internal.create_from_connection_string_sync(
            transport_type, connection_string, ca_certificate.cert
        )
        return self._return_connect_response(internal)

    def create_from_x509_sync(self, transport_type, x509):
        internal = create_glue_object("module", "sync_interface")
        internal.create_from_x509_sync(transport_type, x509)
        return self._return_connect_response(internal)

    def create_from_environment_sync(self, transport_type):
        internal = create_glue_object("module", "sync_interface")
        internal.create_from_environment_sync(transport_type)
        return self._return_connect_response(internal)

    def connect2_sync(self, connection_id):
        self.object_map[connection_id].connect2_sync()

    def reconnect_sync(self, connection_id, force_renew_password):
        self.object_map[connection_id].reconnect_sync(force_renew_password)

    def disconnect2_sync(self, connection_id):
        self.object_map[connection_id].disconnect2_sync()

    def destroy_sync(self, connection_id):
        logger.info("destroying " + connection_id)
        if connection_id in self.object_map:
            internal = self.object_map[connection_id]
            internal.destroy_sync()
            del self.object_map[connection_id]

    def enable_input_messages_sync(self, connection_id):
        self.object_map[connection_id].enable_input_messages_sync()

    def enable_methods_sync(self, connection_id):
        self.object_map[connection_id].enable_methods_sync()

    def enable_twin_sync(self, connection_id):
        self.object_map[connection_id].enable_twin_sync()

    def send_event_sync(self, connection_id, event_body):
        self.object_map[connection_id].send_event_sync(event_body)

    def wait_for_input_message_sync(self, connection_id, input_name):
        response = self.object_map[connection_id].wait_for_input_message_sync(
            input_name
        )
        return EventBody.from_dict(response)

    def invoke_module_method_sync(
        self, connection_id, device_id, module_id, method_invoke_parameters
    ):
        return self.object_map[connection_id].invoke_module_method_sync(
            device_id, module_id, method_invoke_parameters
        )

    def invoke_device_method_sync(
        self, connection_id, device_id, method_invoke_parameters
    ):
        return self.object_map[connection_id].invoke_device_method_sync(
            device_id, method_invoke_parameters
        )

    def wait_for_method_and_return_response_sync(
        self, connection_id, method_name, request_and_response
    ):
        self.object_map[connection_id].wait_for_method_and_return_response_sync(
            method_name, request_and_response
        )

    def send_output_event_sync(self, connection_id, output_name, event_body):
        self.object_map[connection_id].send_output_event_sync(output_name, event_body)

    def wait_for_desired_property_patch_sync(self, connection_id):
        return self.object_map[connection_id].wait_for_desired_property_patch_sync()

    def get_twin_sync(self, connection_id):
        return self.object_map[connection_id].get_twin_sync()

    def send_twin_patch_sync(self, connection_id, props):
        self.object_map[connection_id].send_twin_patch_sync(props)

    def get_connection_status_sync(self, connection_id):
        return self.object_map[connection_id].get_connection_status_sync()

    def wait_for_connection_status_change_sync(self, connection_id, connection_status):
        return self.object_map[connection_id].wait_for_connection_status_change_sync(
            connection_status
        )

    def cleanup_resources_sync(self):
        listcopy = list(self.object_map.keys())
        for key in listcopy:
            logger.info("object {} not cleaned up".format(key))
            self.disconnect_sync(key)
