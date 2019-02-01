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
from ..abstract_device_api import AbstractDeviceApi

# Amount of time to wait after submitting async request.  Gives server time to call API before calling the next API.
wait_time_for_async_start = 1


class DeviceApi(AbstractDeviceApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).device
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

    def send_event(self, body):
        raise NotImplementedError

    @log_entry_and_exit
    @add_timeout
    def disconnect(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(self.connection_id)
            self.connection_id = ""

    @log_entry_and_exit
    @add_timeout
    def enable_methods(self):
        return self.rest_endpoint.enable_methods(self.connection_id)

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
