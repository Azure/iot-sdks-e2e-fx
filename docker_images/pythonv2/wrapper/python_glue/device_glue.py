# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.models.connect_response import ConnectResponse
from swagger_server.models.event_body import EventBody
from internal_glue_factory import create_glue_object
import json
import logging

logger = logging.getLogger(__name__)


class DeviceGlue:
    object_count = 1
    object_map = {}

    def _finish_connection(self, internal):
        connection_id = "deviceObject_" + str(self.object_count)
        self.object_count += 1
        self.object_map[connection_id] = internal
        return ConnectResponse(connection_id)

    def connect_sync(self, transport_type, connection_string, ca_certificate):
        internal = create_glue_object("device", "sync_interface")
        internal.connect_sync(transport_type, connection_string, ca_certificate.cert)
        return self._finish_connection(internal)

    def disconnect_sync(self, connection_id):
        logger.info("disconnecting " + connection_id)
        if connection_id in self.object_map:
            internal = self.object_map[connection_id]
            internal.disconnect_sync()
            del self.object_map[connection_id]

    def create_from_connection_string_sync(
        self, transport_type, connection_string, ca_certificate
    ):
        internal = create_glue_object("device", "sync_interface")
        internal.create_from_connection_string_sync(
            transport_type, connection_string, ca_certificate.cert
        )
        return self._finish_connection(internal)

    def create_from_x509_sync(self, transport_type, x509):
        internal = create_glue_object("device", "sync_interface")
        internal.create_from_x509_sync(transport_type, x509)
        return self._finish_connection(internal)

    def create_from_environment_sync(self, transport_type):
        internal = create_glue_object("device", "sync_interface")
        internal.create_from_environment_sync(transport_type)
        return self._finish_connection(internal)

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

    def enable_methods_sync(self, connection_id):
        self.object_map[connection_id].enable_methods_sync()

    def enable_c2d_sync(self, connection_id):
        self.object_map[connection_id].enable_c2d_sync()

    def send_event_sync(self, connection_id, event_body):
        self.object_map[connection_id].send_event_sync(event_body)

    def wait_for_c2d_message_sync(self, connection_id):
        response = self.object_map[connection_id].wait_for_c2d_message_sync()
        return EventBody.from_dict(response)

    def wait_for_method_and_return_response_sync(
        self, connection_id, method_name, request_and_response
    ):
        self.object_map[connection_id].wait_for_method_and_return_response_sync(
            method_name, request_and_response
        )

    def wait_for_desired_property_patch_sync(self, connection_id):
        return self.object_map[connection_id].wait_for_desired_property_patch_sync()

    def enable_twin_sync(self, connection_id):
        self.object_map[connection_id].enable_twin_sync()

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

    def get_storage_info_for_blob_sync(self, connection_id, blob_name):
        return self.object_map[connection_id].get_storage_info_for_blob_sync(blob_name)

    def notify_blob_upload_status_sync(
        self, connection_id, correlation_id, is_success, status_code, status_description
    ):
        return self.object_map[connection_id].notify_blob_upload_status_sync(
            correlation_id, is_success, status_code, status_description
        )
