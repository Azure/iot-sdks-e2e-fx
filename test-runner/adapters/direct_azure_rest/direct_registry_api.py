# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from ..abstract_iothub_apis import AbstractRegistryApi
from ..decorators import emulate_async
from azure.iot.hub import IoTHubRegistryManager, models


class RegistryApi(AbstractRegistryApi):
    def __init__(self):
        self.registry_manager = None

    async def connect(self, service_connection_string):
        self.registry_manager = IoTHubRegistryManager.from_connection_string(
            service_connection_string
        )

    async def disconnect(self):
        pass

    @emulate_async
    def get_module_twin(self, device_id, module_id):
        return self.registry_manager.get_module_twin(device_id, module_id).as_dict()[
            "properties"
        ]

    @emulate_async
    def patch_module_twin(self, device_id, module_id, patch):
        twin = models.Twin.from_dict({"properties": patch})
        self.registry_manager.update_module_twin(device_id, module_id, twin)

    @emulate_async
    def get_device_twin(self, device_id):
        return self.registry_manager.get_twin(device_id).as_dict()["properties"]

    @emulate_async
    def patch_device_twin(self, device_id, patch):
        twin = models.Twin.from_dict({"properties": patch})
        self.registry_manager.update_twin(device_id, twin)
