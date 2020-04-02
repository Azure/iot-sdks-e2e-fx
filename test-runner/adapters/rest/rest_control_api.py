# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated import e2erestapi
import msrest
from .. import adapter_config
from ..abstract_control_api import AbstractControlApi
from .rest_decorators import log_entry_and_exit

sync_rest_endpoints = None

all_rest_uris = set()


def add_rest_uri(uri):
    global all_rest_uris
    all_rest_uris.add(uri)


def _get_sync_rest_endpoints():
    global all_rest_uris
    global sync_rest_endpoints
    if sync_rest_endpoints is None:
        sync_rest_endpoints = set()
        for uri in all_rest_uris:
            sync_rest_endpoint = e2erestapi.AzureIOTEndToEndTestWrapperRestApi(
                uri
            ).control
            sync_rest_endpoint.config.retry_policy.retries = 0
            sync_rest_endpoints.add(sync_rest_endpoint)

    return sync_rest_endpoints


def cleanup_test_objects_sync():
    for sync_rest_endpoint in _get_sync_rest_endpoints():
        try:
            sync_rest_endpoint.cleanup(timeout=adapter_config.default_api_timeout)
        except Exception:
            pass


class ControlApi(AbstractControlApi):
    def __init__(self, hostname):
        self.sync_rest_endpoint = e2erestapi.AzureIOTEndToEndTestWrapperRestApi(
            hostname
        ).control
        self.sync_rest_endpoint.config.retry_policy.retries = 0

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
    def cleanup_sync(self):
        self.sync_rest_endpoint.cleanup(timeout=adapter_config.default_api_timeout)

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
