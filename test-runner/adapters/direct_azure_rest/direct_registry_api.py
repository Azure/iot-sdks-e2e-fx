# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from ..abstract_iothub_apis import AbstractRegistryApi
from ..decorators import emulate_async
from autorest_service_apis.service20180630modified import (
    IotHubGatewayServiceAPIs20180630 as IotHubGatewayServiceAPIs,
    models,
)
import connection_string
import uuid


class RegistryApi(AbstractRegistryApi):
    def __init__(self):
        self.service = None
        self.service_connection_string = None

    def headers(self):
        cn = connection_string.connection_string_to_sas_token(
            self.service_connection_string
        )
        return {
            "Authorization": cn["sas"],
            "Request-Id": str(uuid.uuid4()),
            "User-Agent": "azure-edge-e2e",
        }

    async def connect(self, service_connection_string):
        self.service_connection_string = service_connection_string
        host = connection_string.connection_string_to_dictionary(
            service_connection_string
        )["HostName"]
        self.service = IotHubGatewayServiceAPIs("https://" + host).service

    async def disconnect(self):
        pass

    @emulate_async
    def get_module_twin(self, device_id, module_id):
        return self.service.get_module_twin(
            device_id, module_id, custom_headers=self.headers()
        ).as_dict()["properties"]

    @emulate_async
    def patch_module_twin(self, device_id, module_id, patch):
        twin = models.Twin.from_dict({"properties": patch})
        self.service.update_module_twin(
            device_id, module_id, twin, custom_headers=self.headers()
        )

    @emulate_async
    def get_device_twin(self, device_id):
        return self.service.get_twin(
            device_id, custom_headers=self.headers()
        ).as_dict()["properties"]

    @emulate_async
    def patch_device_twin(self, device_id, patch):
        twin = models.Twin.from_dict({"properties": patch})
        self.service.update_twin(device_id, twin, custom_headers=self.headers())
