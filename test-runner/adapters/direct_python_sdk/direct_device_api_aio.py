# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..abstract_device_api import AbstractDeviceApi
from azure.iot.hub.devicesdk.aio.async_clients import DeviceClient as DeviceClientAsync
from azure.iot.hub.devicesdk.auth.authentication_provider_factory import from_connection_string


object_list_async = []


class DeviceApiAsync(AbstractDeviceApi):
    def __init__(self):
        self.auth_provider = None
        self.async_client = None

    async def connect(self, transport, connection_string, ca_certificate):
        print("connecting async using " + transport)
        self.auth_provider = from_connection_string(connection_string)
        if ca_certificate and "cert" in ca_certificate:
            self.auth_provider.ca_cert = ca_certificate["cert"]
        self.async_client = await DeviceClientAsync.from_authentication_provider(self.auth_provider, transport)
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
        print("sending event using async")
        await self.async_client.send_event(body)
        print("send confirmation received")

    async def enable_methods(self):
        pass

    async def roundtrip_method_async(self, method_name, status_code, request_payload, response_payload):
        raise NotImplementedError
