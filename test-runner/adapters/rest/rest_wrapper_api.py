#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from multiprocessing.pool import ThreadPool
from multiprocessing.context import TimeoutError
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from ..decorators import add_timeout

rest_endpoints = None

pool = ThreadPool()
print_message_timeout = 2
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
            rest_endpoints.add(rest_endpoint)

    return rest_endpoints


@add_timeout
def cleanup_test_objects():
    for rest_endpoint in _get_rest_endpoints():
        try:
            rest_endpoint.cleanup()
        except Exception:
            pass


def print_message(message):
    """
    log the given message to to stdout on any
    modules that are being used for the current test run.
    """
    for rest_endpoint in _get_rest_endpoints():
        thread = pool.apply_async(
            rest_endpoint.log_message, ({"message": "PYTEST: " + message},)
        )
        try:
            thread.get(print_message_timeout)
        except TimeoutError:
            print("PYTEST: timeout logging to " + str(rest_endpoint))
            # swallow this exception.  logs are allowed to fail (especially if we're testing disconnection scenarios)
