# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
import msrest
from .. import adapter_config
from ..abstract_net_api import AbstractNetApi
from .rest_decorators import log_entry_and_exit
from ..decorators import emulate_async


class NetApi(AbstractNetApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).net
        self.rest_endpoint.config.retry_policy.retries = 0

    @log_entry_and_exit
    def set_destination_sync(self, ip, transport):
        self.rest_endpoint.set_destination(
            ip, transport, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def disconnect(self, disconnect_type):
        self.rest_endpoint.disconnect(
            disconnect_type, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def reconnect(self):
        self.rest_endpoint.reconnect(timeout=adapter_config.default_api_timeout)

    @log_entry_and_exit
    def reconnect_sync(self):
        self.rest_endpoint.reconnect(timeout=adapter_config.default_api_timeout)

    @emulate_async
    @log_entry_and_exit
    def disconnect_after_c2d(self, disconnect_type):
        self.rest_endpoint.disconnect_after_c2d(
            disconnect_type, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def disconnect_after_d2c(self, disconnect_type):
        self.rest_endpoint.disconnect_after_d2c(
            disconnect_type, timeout=adapter_config.default_api_timeout
        )
