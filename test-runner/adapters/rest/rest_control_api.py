# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated.e2erestapi import AzureIOTEndToEndTestWrapperRestApi as GeneratedSyncApi
from .generated.e2erestapi.aio import (
    AzureIOTEndToEndTestWrapperRestApi as GeneratedAsyncApi,
)
import msrest
from .. import adapter_config
from ..abstract_control_api import AbstractControlApi
from .rest_decorators import log_entry_and_exit


class ControlApi(AbstractControlApi):
    def __init__(self, hostname):
        self.sync_rest_endpoint = GeneratedSyncApi(hostname).control
        self.sync_rest_endpoint.config.retry_policy.retries = 0

        self.rest_endpoint = GeneratedAsyncApi(hostname).control
        self.rest_endpoint.config.retry_policy.retries = 0

    def log_message_sync(self, message):
        try:
            self.sync_rest_endpoint.log_message_method(
                {"message": "PYTEST: " + message},
                timeout=adapter_config.print_message_timeout,
            )
        except msrest.exceptions.ClientRequestError:
            print("PYTEST: error logging to " + str(self.sync_rest_endpoint))
            # swallow this exception.  logs are allowed to fail (especially if we're testing disconnection scenarios)

    @log_entry_and_exit
    def get_capabilities_sync(self):
        return self.sync_rest_endpoint.get_capabilities(
            timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def set_flags_sync(self, flags):
        return self.sync_rest_endpoint.set_flags(
            flags, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def send_command_sync(self, cmd):
        return self.sync_rest_endpoint.send_command(
            cmd, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    async def cleanup(self, cmd):
        await self.rest_endpoint.cleanup(
            cmd, timeout=adapter_config.default_api_timeout
        )
