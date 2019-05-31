#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
from ..decorators import log_entry_and_exit
from .. import adapter_config

# Amount of time to wait after submitting async request.  Gives server time to call API before calling the next API.
wait_time_for_async_start = 5


class BaseModuleOrDeviceApi:
    @log_entry_and_exit(print_args=False)
    def connect(self, transport, connection_string, ca_certificate):
        result = self.rest_endpoint.connect(
            transport,
            connection_string,
            ca_certificate=ca_certificate,
            timeout=adapter_config.default_api_timeout,
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def disconnect(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    def enable_twin(self):
        return self.rest_endpoint.enable_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def get_twin(self):
        return self.rest_endpoint.get_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def patch_twin(self, patch):
        self.rest_endpoint.patch_twin(
            self.connection_id, patch, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def wait_for_desired_property_patch_async(self):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_desired_properties_patch),
            (self.connection_id,),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    def enable_methods(self):
        return self.rest_endpoint.enable_methods(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    """
    roundtrip_method_async
    Description: This is a poorly named method. It is essentially create a
    method callback and then wait for a method call.
    """

    @log_entry_and_exit
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
            dict(timeout=adapter_config.default_api_timeout),
        )
        return thread

    @log_entry_and_exit
    def send_event(self, body):
        self.rest_endpoint.send_event(
            self.connection_id, body, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def send_event_async(self, body):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.send_event),
            (self.connection_id, body),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread
