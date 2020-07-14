# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated.e2erestapi.aio import (
    AzureIOTEndToEndTestWrapperRestApi as GeneratedAsyncApi,
)
from .. import adapter_config
from ..abstract_net_api import AbstractNetApi
from .rest_decorators import log_entry_and_exit


class NetApi(AbstractNetApi):
    def __init__(self, hostname):
        self.rest_endpoint = GeneratedAsyncApi(hostname).net
        self.rest_endpoint.config.retry_policy.retries = 0

    @log_entry_and_exit
    async def set_destination(self, ip, transport):
        await self.rest_endpoint.set_destination(
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
