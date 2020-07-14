# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated.e2erestapi.aio import (
    AzureIOTEndToEndTestWrapperRestApi as GeneratedAsyncApi,
)
from .. import adapter_config
from ..abstract_system_control_api import AbstractSystemControlApi
from .rest_decorators import log_entry_and_exit


class SystemControlApi(AbstractSystemControlApi):
    def __init__(self, hostname):
        self.rest_endpoint = GeneratedAsyncApi(hostname).system_control
        self.rest_endpoint.config.retry_policy.retries = 0

    @log_entry_and_exit
    async def set_network_destination(self, ip, transport):
        await self.rest_endpoint.set_network_destination(
            ip, transport, timeout=adapter_config.control_api_timeout
        )

    @log_entry_and_exit
    async def disconnect_network(self, disconnect_type):
        await self.rest_endpoint.disconnect_network(
            disconnect_type, timeout=adapter_config.control_api_timeout
        )

    @log_entry_and_exit
    async def reconnect_network(self):
        await self.rest_endpoint.reconnect_network(
            timeout=adapter_config.control_api_timeout
        )

    @log_entry_and_exit
    async def get_system_stats(self, wrapper_pid):
        await self.rest_endpoint.get_system_stats(
            timeout=adapter_config.control_api_timeout
        )
