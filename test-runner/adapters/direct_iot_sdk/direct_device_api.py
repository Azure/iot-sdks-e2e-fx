# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from adapters.abstract_device_api import AbstractDeviceApi
from azure.iot.hub.devicesdk.sync_clients import DeviceClient as DeviceClientSync
from azure.iot.hub.devicesdk.auth.authentication_provider_factory import from_connection_string

object_list_sync = []


class DeviceApi(AbstractDeviceApi):
    def __init__(self):
        self.auth_provider = None
        self.sync_client = None
        self.async_client = None

    def connect(self, transport, connection_string, ca_certificate):
        print("connecting using " + transport)
        self.auth_provider = from_connection_string(connection_string)
        if ca_certificate and "cert" in ca_certificate:
            self.auth_provider.ca_cert = ca_certificate["cert"]
        self.sync_client = DeviceClientSync.from_authentication_provider(self.auth_provider, transport)
        object_list_sync.append(self)
        self.sync_client.connect()

    def disconnect(self):
        if self in object_list_sync:
            object_list_sync.remove(self)

        self.sync_client.disconnect()
        self.sync_client = None

        self.auth_provider.disconnect()
        self.auth_provider = None

    def send_event(self, body):
        print("sending event")
        self.sync_client.send_event(body)
        print("send confirmation received")

    def enable_methods(self):
        raise NotImplementedError

    def roundtrip_method_async(self, method_name, status_code, request_payload, response_payload):
        raise NotImplementedError
