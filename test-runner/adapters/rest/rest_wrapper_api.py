#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
import msrest
from .. import adapter_config

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
            rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(uri).wrapper
            rest_endpoint.config.retry_policy.retries = 0
            rest_endpoints.add(rest_endpoint)

    return rest_endpoints


def cleanup_test_objects():
    for rest_endpoint in _get_rest_endpoints():
        try:
            rest_endpoint.cleanup(timeout=adapter_config.default_api_timeout)
        except Exception:
            pass


def print_message(message):
    """
    log the given message to to stdout on any
    modules that are being used for the current test run.
    """
    for rest_endpoint in _get_rest_endpoints():
        try:
            rest_endpoint.log_message(
                {"message": "PYTEST: " + message},
                timeout=adapter_config.print_message_timeout,
            )
        except msrest.exceptions.ClientRequestError:
            print("PYTEST: error logging to " + str(rest_endpoint))
            # swallow this exception.  logs are allowed to fail (especially if we're testing disconnection scenarios)
