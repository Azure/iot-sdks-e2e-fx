#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from multiprocessing.pool import ThreadPool
from ..decorators import log_entry_and_exit
from .. import adapter_config
from ..abstract_module_api import AbstractModuleApi
from .base_module_or_device_api import BaseModuleOrDeviceApi

# Amount of time to wait after submitting async request.  Gives server time to call API before calling the next API.
wait_time_for_async_start = 5


class ModuleApi(BaseModuleOrDeviceApi, AbstractModuleApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).module
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()

    @log_entry_and_exit
    def connect_from_environment(self, transport):
        result = self.rest_endpoint.connect_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def send_output_event(self, output_name, body):
        self.rest_endpoint.send_output_event(
            self.connection_id,
            output_name,
            body,
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    def enable_input_messages(self):
        return self.rest_endpoint.enable_input_messages(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def wait_for_input_event_async(self, input_name):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_input_message),
            (self.connection_id, input_name),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_module_method),
            (self.connection_id, device_id, module_id, method_invoke_parameters),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    def call_device_method_async(self, device_id, method_invoke_parameters):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_device_method),
            (self.connection_id, device_id, method_invoke_parameters),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread
