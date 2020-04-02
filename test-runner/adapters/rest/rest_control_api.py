# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from .generated.e2erestapi import AzureIOTEndToEndTestWrapperRestApi
import msrest
from .. import adapter_config
from ..abstract_control_api import AbstractControlApi
from .rest_decorators import log_entry_and_exit

rest_endpoints = None

all_rest_uris = set()


def add_rest_uri(uri):
    global all_rest_uris
    all_rest_uris.add(uri)


def _get_rest_endpoints():
    global all_rest_uris
    global rest_endpoints
    if rest_endpoints is None:
        rest_endpoints = set()
        for uri in all_rest_uris:
            rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(uri).control
            rest_endpoint.config.retry_policy.retries = 0
            rest_endpoints.add(rest_endpoint)

    return rest_endpoints


def cleanup_test_objects():
    for rest_endpoint in _get_rest_endpoints():
        try:
            rest_endpoint.cleanup(timeout=adapter_config.default_api_timeout)
        except Exception:
            pass


class ControlApi(AbstractControlApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).control
        self.rest_endpoint.config.retry_policy.retries = 0

    def log_message_sync(self, message):
        try:
            self.rest_endpoint.log_message_method(
                {"message": "PYTEST: " + message},
                timeout=adapter_config.print_message_timeout,
            )
        except msrest.exceptions.ClientRequestError:
            print("PYTEST: error logging to " + str(self.rest_endpoint))
            # swallow this exception.  logs are allowed to fail (especially if we're testing disconnection scenarios)

    @log_entry_and_exit
    def cleanup_sync(self):
        self.rest_endpoint.cleanup(timeout=adapter_config.default_api_timeout)

    @log_entry_and_exit
    def get_capabilities_sync(self):
        return self.rest_endpoint.get_capabilities(
            timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def set_flags_sync(self, flags):
        return self.rest_endpoint.set_flags(
            flags, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def send_command_sync(self, cmd):
        return self.rest_endpoint.send_command(
            cmd, timeout=adapter_config.default_api_timeout
        )
