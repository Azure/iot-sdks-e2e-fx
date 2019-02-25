#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from multiprocessing.pool import ThreadPool
from ..decorators import log_entry_and_exit, add_timeout
from ..abstract_module_api import AbstractModuleApi

# Amount of time to wait after submitting async request.  Gives server time to call API before calling the next API.
wait_time_for_async_start = 5


class ModuleApi(AbstractModuleApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).module
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()

    @log_entry_and_exit(print_args=False)
    @add_timeout
    def connect(self, transport, connection_string, ca_certificate):
        result = self.rest_endpoint.connect(
            transport, connection_string, ca_certificate=ca_certificate
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    @add_timeout
    def connect_from_environment(self, transport):
        result = self.rest_endpoint.connect_from_environment(transport)
        self.connection_id = result.connection_id

    @log_entry_and_exit
    @add_timeout
    def disconnect(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(self.connection_id)
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    @add_timeout
    def enable_twin(self):
        return self.rest_endpoint.enable_twin(self.connection_id)

    @log_entry_and_exit
    @add_timeout
    def enable_methods(self):
        return self.rest_endpoint.enable_methods(self.connection_id)

    @log_entry_and_exit
    @add_timeout
    def enable_input_messages(self):
        return self.rest_endpoint.enable_input_messages(self.connection_id)

    """
    *NOTE FOR C SDK*
    get_twin is not fully implemented in C SDK, so this function is just glue code
    that wraps the twin snippet and returns it, never calling into the SDK itself.
    """

    @log_entry_and_exit
    @add_timeout
    def get_twin(self):
        return self.rest_endpoint.get_twin(self.connection_id)

    @log_entry_and_exit
    @add_timeout
    def patch_twin(self, patch):
        self.rest_endpoint.patch_twin(self.connection_id, patch)

    @log_entry_and_exit
    @add_timeout
    def wait_for_desired_property_patch_async(self):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_desired_properties_patch),
            (self.connection_id,),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    @add_timeout
    def send_event(self, body):
        self.rest_endpoint.send_event(self.connection_id, body)

    @log_entry_and_exit
    @add_timeout
    def send_event_async(self, body):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.send_event),
            (self.connection_id, body),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    @add_timeout
    def send_output_event(self, output_name, body):
        self.rest_endpoint.send_output_event(self.connection_id, output_name, body)

    @log_entry_and_exit
    @add_timeout
    def wait_for_input_event_async(self, input_name):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_input_message),
            (self.connection_id, input_name),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    @add_timeout
    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_module_method),
            (self.connection_id, device_id, module_id, method_invoke_parameters),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    @add_timeout
    def call_device_method_async(self, device_id, method_invoke_parameters):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_device_method),
            (self.connection_id, device_id, method_invoke_parameters),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    """
    roundtrip_method_async
    Description: This is a poorly named method. It is essentially create a
    method callback and then wait for a method call.
    """

    @log_entry_and_exit
    @add_timeout
    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        request_and_response = {
            "requestPayload": request_payload,
            "responsePayload": response_payload,
            "statusCode": status_code,
        }
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.roundtrip_method_call),
            (self.connection_id, method_name, request_and_response),
        )
        return thread
