#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from multiprocessing.pool import ThreadPool
from ..decorators import log_entry_and_exit, add_timeout


class ServiceApi:
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).service
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()

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
    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        return self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_module_method),
            (self.connection_id, device_id, module_id, method_invoke_parameters),
        )

    @log_entry_and_exit
    @add_timeout
    def call_device_method_async(self, device_id, method_invoke_parameters):
        return self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_device_method),
            (self.connection_id, device_id, method_invoke_parameters),
        )
