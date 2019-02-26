#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
from environment import runtime_config
import runtime_configuration_templates as config


def connect_test_module_client():
    """
    connect the module client for the code-under-test and return the client object
    """
    client = adapters.TestModuleClient()
    if runtime_config.test_module.connection_type == config.ENVIRONMENT:
        client.connect_from_environment(runtime_config.test_module.transport)
    else:
        client.connect(
            runtime_config.test_module.transport,
            runtime_config.test_module.connection_string,
            runtime_config.ca_certificate,
        )
    return client


def connect_friend_module_client():
    """
    connect the module client for the friend module and return the client object
    """
    client = adapters.FriendModuleClient()
    if runtime_config.friend_module.connection_type == config.ENVIRONMENT:
        client.connect_from_environment(runtime_config.friend_module.transport)
    else:
        client.connect(
            runtime_config.friend_module.transport,
            runtime_config.friend_module.connection_string,
            runtime_config.ca_certificate,
        )
    return client


def connect_eventhub_client():
    """
    connect the module client for the EventHub implementation we're using return the client object
    """
    client = adapters.EventHubClient()
    client.connect(runtime_config.eventhub.connection_string)
    return client


def connect_registry_client():
    """
    connect the module client for the Registry implementation we're using return the client object
    """
    client = adapters.RegistryClient()
    client.connect(runtime_config.registry.connection_string)
    return client


def connect_service_client():
    """
    connect the module client for the ServiceClient implementation we're using return the client object
    """
    client = adapters.ServiceClient()
    client.connect(runtime_config.service.connection_string)
    return client


def connect_leaf_device_client():
    """
    connect the device client for the leaf device and return the client object
    """
    client = adapters.LeafDeviceClient()
    client.connect(
        runtime_config.leaf_device.transport,
        runtime_config.leaf_device.connection_string,
        runtime_config.ca_certificate,
    )
    return client
