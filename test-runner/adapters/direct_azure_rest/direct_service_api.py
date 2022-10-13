# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from ..abstract_iothub_apis import AbstractServiceApi
from ..decorators import emulate_async
from .amqp_service_client import AmqpServiceClient
from azure.iot.hub import IoTHubRegistryManager, models


class ServiceApi(AbstractServiceApi):
    def __init__(self):
        self.service_connection_string = None
        self.amqp_service_client = None
        self.registry_manager = None

    async def connect(self, service_connection_string):
        self.service_connection_string = service_connection_string
        self.registry_manager = IoTHubRegistryManager.from_connection_string(
            service_connection_string
        )

    async def disconnect(self):
        if self.amqp_service_client:
            await self.amqp_service_client.disconnect()
            self.amqp_serice_client = None
        self.registry_manager = None

    @emulate_async
    def call_module_method(self, device_id, module_id, method_invoke_parameters):
        return self.registry_manager.invoke_device_module_method(
            device_id,
            module_id,
            models.CloudToDeviceMethod.from_dict(method_invoke_parameters),
        ).as_dict()

    @emulate_async
    def call_device_method(self, device_id, method_invoke_parameters):
        return self.registry_manager.invoke_device_method(
            device_id, models.CloudToDeviceMethod.from_dict(method_invoke_parameters)
        ).as_dict()

    async def send_c2d(self, device_id, message):
        if not self.amqp_service_client:
            self.amqp_service_client = AmqpServiceClient()
            await self.amqp_service_client.connect(self.service_connection_string)
        await self.amqp_service_client.send_to_device(device_id, message)

    async def get_blob_upload_status(self):
        if not self.amqp_service_client:
            self.amqp_service_client = AmqpServiceClient()
            await self.amqp_service_client.connect(self.service_connection_string)
        return await self.amqp_service_client.get_next_blob_status()
