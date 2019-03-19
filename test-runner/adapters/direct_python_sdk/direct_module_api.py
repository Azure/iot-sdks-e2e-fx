#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import base64
import json
from multiprocessing.pool import ThreadPool
from internal_module_glue import InternalModuleGlue
from ..print_message import print_message
from ..abstract_module_api import AbstractModuleApi

object_list = []


class ModuleApi(AbstractModuleApi):
    def __init__(self):
        self.glue = InternalModuleGlue()
        self.pool = ThreadPool()

    def connect(self, transport, connection_string, ca_certificate):
        object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        self.glue.connect(transport, connection_string, cert)

    def connect_from_environment(self, transport):
        object_list.append(self)
        self.glue.connect_from_environment(transport)

    def disconnect(self):
        if self in object_list:
            object_list.remove(self)

        self.glue.disconnect()
        self.glue = None

    def enable_twin(self):
        self.glue.enable_twin()

    def enable_methods(self):
        self.glue.enable_methods()

    def enable_input_messages(self):
        self.glue.enable_input_messages()

    def get_twin(self):
        return self.glue.get_twin()

    def patch_twin(self, patch):
        self.glue.patch_twin(patch)

    def wait_for_desired_property_patch_async(self):
        return self.glue.wait_for_desired_property_patch()

    def send_event(self, body):
        self.glue.send_event(body)

    def send_event_async(self, body):
        raise NotImplementedError()

    def send_output_event(self, output_name, body):
        self.glue.send_output_event(output_name, body)

    def wait_for_input_event_async(self, input_name):
        return self.pool.apply_async(self.glue.wait_for_input_message, (input_name,))

    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        return self.pool.apply_async(
            self.glue.invoke_module_method,
            (device_id, module_id, method_invoke_parameters),
        )

    def call_device_method_async(self, device_id, method_invoke_parameters):
        return self.pool.apply_async(
            self.glue.invoke_device_method, (device_id, method_invoke_parameters)
        )

    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        raise NotImplementedError()
