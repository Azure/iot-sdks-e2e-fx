#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from ..abstract_registry_api import AbstractRegistryApi
from autorest_service_apis.service20180630modified import (
    IotHubGatewayServiceAPIs20180630 as IotHubGatewayServiceAPIs,
    models,
)
import connection_string
import uuid

object_list = []


class RegistryApi:
    def __init__(self):
        global object_list
        object_list.append(self)
        self.cn = None
        self.service = None

    def headers(self):
        return {
            "Authorization": self.cn["sas"],
            "Request-Id": str(uuid.uuid4()),
            "User-Agent": "azure-edge-e2e",
        }

    def connect(self, service_connection_string):
        self.cn = connection_string.connection_string_to_sas_token(
            service_connection_string
        )
        self.service = IotHubGatewayServiceAPIs("https://" + self.cn["host"]).service

    def disconnect(self):
        pass

    def get_module_twin(self, device_id, module_id):
        return self.service.get_module_twin(
            device_id, module_id, custom_headers=self.headers()
        ).as_dict()

    def patch_module_twin(self, device_id, module_id, patch):
        twin = models.Twin.from_dict(patch)
        self.service.update_module_twin(
            device_id, module_id, twin, custom_headers=self.headers()
        )

    def get_device_twin(self, device_id):
        return self.service.get_twin(device_id, custom_headers=self.headers()).as_dict()

    def patch_device_twin(self, device_id, patch):
        twin = models.Twin.from_dict(patch)
        self.service.update_twin(device_id, twin, custom_headers=self.headers())
