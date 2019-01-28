#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from ..decorators import log_entry_and_exit, add_timeout


class RegistryApi:
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).registry
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""

    @log_entry_and_exit(print_args=False)
    @add_timeout
    def connect(self, connection_string):
        result = self.rest_endpoint.connect(connection_string)
        self.connection_id = result.connection_id

    @log_entry_and_exit
    @add_timeout
    def disconnect(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(self.connection_id)
            self.connection_id = ""

    @log_entry_and_exit
    @add_timeout
    def get_module_twin(self, device_id, module_id):
        return self.rest_endpoint.get_module_twin(
            self.connection_id, device_id, module_id
        )

    @log_entry_and_exit
    @add_timeout
    def patch_module_twin(self, device_id, module_id, patch):
        self.rest_endpoint.patch_module_twin(
            self.connection_id, device_id, module_id, patch
        )
