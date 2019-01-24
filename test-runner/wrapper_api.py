#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import environment
from multiprocessing.pool import ThreadPool
from multiprocessing.context import TimeoutError
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from decorators import add_timeout

rest_endpoints = None

pool = ThreadPool()
print_message_timeout = 2


def get_rest_endpoints():
    global rest_endpoints
    if rest_endpoints == None:
        hosts = set(
            [
                environment.test_module_uri,
                environment.friend_module_uri,
                environment.leaf_device_uri,
                environment.eventhub_uri,
                environment.service_client_uri,
                environment.registry_uri,
            ]
        )

        rest_endpoints = set()
        for host in hosts:
            rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(host).wrapper
            rest_endpoints.add(rest_endpoint)

    return rest_endpoints


@add_timeout
def cleanup_after_test_case():
    exception_to_throw = None
    for rest_endpoint in get_rest_endpoints():
        try:
            rest_endpoint.cleanup()
        except Exception as e:
            exception_to_throw = e
    if exception_to_throw != None:
        raise exception_to_throw # pylint: disable=raising-bad-type 


@add_timeout
def session_start():
    # not what we really want to do, but OK for now
    for rest_endpoint in get_rest_endpoints():
        try:
            rest_endpoint.cleanup()
        except:
            pass


def session_end():
    pass


def print_message(message):
    """
    log the given message to stdout on the current process and also to stdout on any 
    modules that are being used for the current test run.
    """
    print("PYTEST: " + message)
    for rest_endpoint in get_rest_endpoints():
        thread = pool.apply_async(
            rest_endpoint.log_message, ({"message": "PYTEST: " + message},)
        )
        try:
            thread.get(print_message_timeout)
        except TimeoutError:
            print("PYTEST: timeout logging to " + str(rest_endpoint))
            # swallow this exception.  logs are allowed to fail (especially if we're testing disconnection scenarios)
