# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from autorest_service_apis.service20180630modified import (
    IotHubGatewayServiceAPIs20180630 as IotHubGatewayServiceAPIs,
)
from ..abstract_iothub_apis import AbstractServiceApi
from ..decorators import emulate_async
import connection_string
import uuid
from .amqp_service_client import AmqpServiceClient


class ServiceApi(AbstractServiceApi):
    def __init__(self):
        self.service = None
        self.service_connection_string = None
        self.amqp_service_client = None

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
        if self.amqp_service_client:
            await self.amqp_service_client.disconnect()
            self.amqp_serice_client = None
        self.service = None

    @emulate_async
    def call_module_method(self, device_id, module_id, method_invoke_parameters):
        return self.service.invoke_device_method1(
            device_id,
            module_id,
            method_invoke_parameters,
            custom_headers=self.headers(),
        ).as_dict()

    @emulate_async
    def call_device_method(self, device_id, method_invoke_parameters):
        return self.service.invoke_device_method(
            device_id, method_invoke_parameters, custom_headers=self.headers()
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
