# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated.e2erestapi import AzureIOTEndToEndTestWrapperRestApi as GeneratedSyncApi
from .generated.e2erestapi.aio import (
    AzureIOTEndToEndTestWrapperRestApi as GeneratedAsyncApi,
)
import msrest
from .. import adapter_config
from ..abstract_net_api import AbstractNetApi
from .rest_decorators import log_entry_and_exit


class NetApi(AbstractNetApi):
    def __init__(self, hostname):
        self.rest_endpoint = GeneratedAsyncApi(hostname).net
        self.rest_endpoint.config.retry_policy.retries = 0

        self.rest_endpoint_sync = GeneratedSyncApi(hostname).net
        self.rest_endpoint_sync.config.retry_policy.retries = 0

    @log_entry_and_exit
    def set_destination_sync(self, ip, transport):
        self.rest_endpoint_sync.set_destination(
            ip, transport, timeout=adapter_config.control_api_timeout
        )

    @log_entry_and_exit
    async def disconnect(self, disconnect_type):
        await self.rest_endpoint.disconnect(
            disconnect_type, timeout=adapter_config.control_api_timeout
        )

    @log_entry_and_exit
    async def reconnect(self):
        await self.rest_endpoint.reconnect(timeout=adapter_config.control_api_timeout)

    @log_entry_and_exit
    def reconnect_sync(self):
        self.rest_endpoint_sync.reconnect(timeout=adapter_config.control_api_timeout)

    @log_entry_and_exit
    async def disconnect_after_c2d(self, disconnect_type):
        await self.rest_endpoint.disconnect_after_c2d(
            disconnect_type, timeout=adapter_config.control_api_timeout
        )

    @log_entry_and_exit
    async def disconnect_after_d2c(self, disconnect_type):
        await self.rest_endpoint.disconnect_after_d2c(
            disconnect_type, timeout=adapter_config.control_api_timeout
        )
