#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import base64
import json
from ..print_message import print_message
from ..abstract_module_api import AbstractModuleApi
from azure.iot.hub.devicesdk.sync_clients import ModuleClient as ModuleClientSync
from azure.iot.hub.devicesdk.auth.authentication_provider_factory import (
    from_connection_string,
    from_environment,
)

# logging.basicConfig(level=logging.INFO)

object_list_sync = []


class ModuleApi(AbstractModuleApi):
    def __init__(self):
        self.auth_provider = None
        self.sync_client = None
        self.async_client = None

    def connect(self, transport, connection_string, ca_certificate):
        print("connecting using " + transport)
        self.auth_provider = from_connection_string(connection_string)
        if ca_certificate and "cert" in ca_certificate:
            self.auth_provider.ca_cert = ca_certificate["cert"]
        self.sync_client = ModuleClientSync.from_authentication_provider(
            self.auth_provider, transport
        )
        object_list_sync.append(self)
        self.sync_client.connect()

    def connect_from_environment(self, transport):
        print("connecting from environment")
        self.auth_provider = from_environment()
        self.sync_client = ModuleClientSync.from_authentication_provider(
            self.auth_provider, transport
        )
        object_list_sync.append(self)
        self.sync_client.connect()

    def disconnect(self):
        if self in object_list_sync:
            object_list_sync.remove(self)

        self.sync_client.disconnect()
        self.sync_client = None

        self.auth_provider.disconnect()
        self.auth_provider = None

    def enable_twin(self):
        raise NotImplementedError()

    def enable_methods(self):
        raise NotImplementedError()

    def enable_input_messages(self):
        # TODO : Should take input name as param ?
        input_message_queue = self.sync_client.get_input_message_queue("input1")

    def get_twin(self):
        raise NotImplementedError()

    def patch_twin(self, patch):
        raise NotImplementedError()

    def wait_for_desired_property_patch_async(self):
        raise NotImplementedError()

    def send_event(self, body):
        print("sending event")
        self.sync_client.send_event(body)
        print("send confirmation received")

    def send_output_event(self, output_name, body):
        print("sending output event")
        if isinstance(body, str):
            body = json.dumps(body)
        self.sync_client.send_to_output(body, output_name)
        print("send confirmation received")

    def wait_for_input_event_async(self, input_name):
        raise NotImplementedError()

    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        raise NotImplementedError()

    def call_device_method_async(self, device_id, method_invoke_parameters):
        raise NotImplementedError()

    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        raise NotImplementedError()
