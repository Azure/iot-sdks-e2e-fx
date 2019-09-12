# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from multiprocessing.pool import ThreadPool
from autorest_service_apis.service20180630modified import (
    IotHubGatewayServiceAPIs20180630 as IotHubGatewayServiceAPIs,
)
from ..abstract_service_api import AbstractServiceApi
import connection_string
import uuid
from .amqp_service_client import AmqpServiceClient

object_list = []


class ServiceApi(AbstractServiceApi):
    def __init__(self):
        global object_list
        object_list.append(self)
        self.cn = None
        self.service = None
        self.service_connection_string = None
        self.amqp_service_client = None
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()

    def headers(self):
        return {
            "Authorization": self.cn["sas"],
            "Request-Id": str(uuid.uuid4()),
            "User-Agent": "azure-edge-e2e",
        }

    def connect(self, service_connection_string):
        self.service_connection_string = service_connection_string
        self.cn = connection_string.connection_string_to_sas_token(
            service_connection_string
        )
        self.service = IotHubGatewayServiceAPIs("https://" + self.cn["host"]).service

    def disconnect(self):
        if self.amqp_service_client:
            self.amqp_service_client.disconnect()
            self.amqp_serice_client = None
        self.cn = None
        self.service = None

    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        def thread_proc():
            return self.service.invoke_device_method1(
                device_id,
                module_id,
                method_invoke_parameters,
                custom_headers=self.headers(),
            ).as_dict()

        return self.pool.apply_async(thread_proc)

    def call_device_method_async(self, device_id, method_invoke_parameters):
        def thread_proc():
            return self.service.invoke_device_method(
                device_id, method_invoke_parameters, custom_headers=self.headers()
            ).as_dict()

        return self.pool.apply_async(thread_proc)

    def send_c2d(self, device_id, message):
        if not self.amqp_service_client:
            self.amqp_service_client = AmqpServiceClient()
            self.amqp_service_client.connect(self.service_connection_string)
        self.amqp_service_client.send_to_device(device_id, message)
