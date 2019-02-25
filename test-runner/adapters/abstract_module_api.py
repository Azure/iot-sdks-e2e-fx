#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractModuleApi:
    @abc.abstractmethod
    async def connect(self, transport, connection_string, ca_certificate):
        pass

    @abc.abstractmethod
    async def connect_from_environment(self, transport):
        pass

    @abc.abstractmethod
    async def disconnect(self):
        pass

    @abc.abstractmethod
    async def enable_twin(self):
        pass

    @abc.abstractmethod
    async def enable_methods(self):
        pass

    @abc.abstractmethod
    async def enable_input_messages(self):
        pass

    @abc.abstractmethod
    async def get_twin(self):
        pass

    @abc.abstractmethod
    async def patch_twin(self, patch):
        pass

    @abc.abstractmethod
    async def wait_for_desired_property_patch_async(self):
        pass

    @abc.abstractmethod
    async def send_event(self, body):
        pass

    @abc.abstractmethod
    async def send_output_event(self, output_name, body):
        pass

    @abc.abstractmethod
    async def wait_for_input_event_async(self, input_name):
        pass

    @abc.abstractmethod
    async def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        pass

    @abc.abstractmethod
    async def call_device_method_async(self, device_id, method_invoke_parameters):
        pass

    @abc.abstractmethod
    async def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        pass
