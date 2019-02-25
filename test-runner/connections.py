#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
import environment


def connect_test_module_client():
    """
    connect the module client for the code-under-test and return the client object
    """
    client = adapters.TestModuleClient()
    if environment.test_module_connect_from_environment:
        client.connect_from_environment(environment.test_module_transport)
    else:
        client.connect(
            environment.test_module_transport,
            environment.test_module_connection_string,
            environment.ca_certificate,
        )
    return client


async def connect_test_module_client_async():
    """
    connect the module client for the code-under-test and return the client object
    """
    client = adapters.TestModuleClientAsync()
    if environment.test_module_connect_from_environment:
        await client.connect_from_environment(environment.test_module_transport)
    else:
        await client.connect(
            environment.test_module_transport,
            environment.test_module_connection_string,
            environment.ca_certificate,
        )
    return client


def connect_friend_module_client():
    """
    connect the module client for the friend module and return the client object
    """
    client = adapters.FriendModuleClient()
    if environment.friend_module_connect_from_environment:
        client.connect_from_environment(environment.friend_module_transport)
    else:
        client.connect(
            environment.friend_module_transport,
            environment.friend_module_connection_string,
            environment.ca_certificate,
        )
    return client


def connect_eventhub_client():
    """
    connect the module client for the EventHub implementation we're using return the client object
    """
    client = adapters.EventHubClient()
    client.connect(environment.service_connection_string)
    return client


def connect_registry_client():
    """
    connect the module client for the Registry implementation we're using return the client object
    """
    client = adapters.RegistryClient()
    client.connect(environment.service_connection_string)
    return client


def connect_service_client():
    """
    connect the module client for the ServiceClient implementation we're using return the client object
    """
    client = adapters.ServiceClient()
    client.connect(environment.service_connection_string)
    return client


def connect_leaf_device_client():
    """
    connect the device client for the leaf device and return the client object
    """
    client = adapters.LeafDeviceClient()
    client.connect(
        environment.leaf_device_transport,
        environment.leaf_device_connection_string,
        environment.ca_certificate,
    )
    return client


async def connect_leaf_device_client_async():
    """
    connect the device client for the leaf device and return the client object
    """
    client = adapters.LeafDeviceClientAsync()
    await client.connect(
        environment.leaf_device_transport,
        environment.leaf_device_connection_string,
        environment.ca_certificate,
    )
    return client
