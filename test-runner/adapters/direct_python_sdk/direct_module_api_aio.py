#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import base64
from ..print_message import print_message
import json
from ..abstract_module_api import AbstractModuleApi
from azure.iot.hub.devicesdk.aio.async_clients import ModuleClient as ModuleClientAsync
from azure.iot.hub.devicesdk.auth.authentication_provider_factory import (
    from_connection_string,
    from_environment,
)

# logging.basicConfig(level=logging.INFO)

object_list_async = []


class ModuleApiAsync(AbstractModuleApi):
    def __init__(self):
        self.auth_provider = None
        self.async_client = None

    async def connect(self, transport, connection_string, ca_certificate):
        print("connecting using " + transport)
        self.auth_provider = from_connection_string(connection_string)
        if ca_certificate and "cert" in ca_certificate:
            self.auth_provider.ca_cert = ca_certificate["cert"]
        self.async_client = await ModuleClientAsync.from_authentication_provider(
            self.auth_provider, transport
        )
        object_list_async.append(self)
        await self.async_client.connect()

    async def connect_from_environment(self, transport):
        print("connecting from environment")
        self.auth_provider = from_environment()
        self.async_client = await ModuleClientAsync.from_authentication_provider(
            self.auth_provider, transport
        )
        object_list_async.append(self)
        await self.async_client.connect()

    async def disconnect(self):
        if self in object_list_async:
            object_list_async.remove(self)

        await self.async_client.disconnect()
        self.async_client = None

        self.auth_provider.disconnect()
        self.auth_provider = None

    async def send_event(self, body):
        print("sending event")
        await self.async_client.send_event(body)
        print("send confirmation received")

    async def enable_twin(self):
        raise NotImplementedError()

    async def enable_methods(self):
        raise NotImplementedError()

    async def enable_input_messages(self):
        raise NotImplementedError()

    async def get_twin(self):
        raise NotImplementedError()

    async def patch_twin(self, patch):
        raise NotImplementedError()

    async def wait_for_desired_property_patch_async(self):
        raise NotImplementedError()

    async def send_output_event(self, output_name, body):
        print("sending output event")
        if isinstance(body, str):
            body = json.dumps(body)
        await self.async_client.send_to_output(body, output_name)
        print("send confirmation received")

    async def wait_for_input_event_async(self, input_name):
        raise NotImplementedError()

    async def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        raise NotImplementedError()

    async def call_device_method_async(self, device_id, method_invoke_parameters):
        raise NotImplementedError()

    async def roundtrip_method_async(
            self, method_name, status_code, request_payload, response_payload
    ):
        raise NotImplementedError()
