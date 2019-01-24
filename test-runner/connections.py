#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from module_api import ModuleApi
from eventhub_api import EventHubApi
from service_api import ServiceApi
from registry_api import RegistryApi
from device_api import DeviceApi
import environment


def call_connect_api(
    api, useEnvironment, transport, connectionString=None, certificate=None
):
    """
    call the connect api for the given parameters
    """
    if useEnvironment:
        api.connect_from_environment(transport)
    else:
        api.connect(transport, connectionString, certificate)


def create_and_connect_api_client(Api, args):
    """
    Create an instance of an Api client and connect it, returning a client object
    """
    api_client = Api(args["hostUri"])
    args["connect"](api_client)
    return api_client


def connect_test_module_client():
    """
    connect the module client for the code-under-test and return the client object
    """
    test_module_connection_args = {
        "connect": lambda module: call_connect_api(
            module,
            environment.test_module_connect_from_environment,
            environment.test_module_transport,
            environment.test_module_connection_string,
            environment.ca_certificate,
        ),
        "hostUri": environment.test_module_uri,
    }
    return create_and_connect_api_client(ModuleApi, test_module_connection_args)


def connect_friend_module_client():
    """
    connect the module client for the friend module and return the client object
    """
    friend_module_connection_args = {
        "connect": lambda module: call_connect_api(
            module,
            environment.friend_module_connect_from_environment,
            environment.friend_module_transport,
            environment.friend_module_connection_string,
            environment.ca_certificate,
        ),
        "hostUri": environment.friend_module_uri,
    }
    return create_and_connect_api_client(ModuleApi, friend_module_connection_args)


def connect_eventhub_client():
    """
    connect the module client for the EventHub implementation we're using return the client object
    """
    eventhub_connection_args = {
        "connect": lambda eventhub: eventhub.connect(
            environment.service_connection_string
        ),
        "hostUri": environment.eventhub_uri,
    }
    return create_and_connect_api_client(EventHubApi, eventhub_connection_args)


def connect_registry_client():
    """
    connect the module client for the Registry implementation we're using return the client object
    """
    registry_connection_args = {
        "connect": lambda registry: registry.connect(
            environment.service_connection_string
        ),
        "hostUri": environment.registry_uri,
    }
    return create_and_connect_api_client(RegistryApi, registry_connection_args)


def connect_service_client():
    """
    connect the module client for the ServiceClient implementation we're using return the client object
    """
    service_client_connection_args = {
        "connect": lambda client: client.connect(environment.service_connection_string),
        "hostUri": environment.service_client_uri,
    }
    return create_and_connect_api_client(ServiceApi, service_client_connection_args)


def connect_leaf_device_client():
    """
    connect the device client for the leaf device and return the client object
    """
    leaf_device_connection_args = {
        "connect": lambda client: client.connect(
            environment.leaf_device_transport,
            environment.leaf_device_connection_string,
            environment.ca_certificate,
        ),
        "hostUri": environment.leaf_device_uri,
    }
    return create_and_connect_api_client(DeviceApi, leaf_device_connection_args)
