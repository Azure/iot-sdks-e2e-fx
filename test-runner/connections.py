#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
import runtime_config
import runtime_config_templates


def connect_test_module_client():
    """
    connect the module client for the code-under-test and return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.TestModuleClient()
    if (
        current_config.test_module.connection_type
        == runtime_config_templates.ENVIRONMENT
    ):
        client.connect_from_environment(current_config.test_module.transport)
    else:
        client.connect(
            current_config.test_module.transport,
            current_config.test_module.connection_string,
            current_config.ca_certificate,
        )
    return client


def connect_friend_module_client():
    """
    connect the module client for the friend module and return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.FriendModuleClient()
    if (
        current_config.friend_module.connection_type
        == runtime_config_templates.ENVIRONMENT
    ):
        client.connect_from_environment(current_config.friend_module.transport)
    else:
        client.connect(
            current_config.friend_module.transport,
            current_config.friend_module.connection_string,
            current_config.ca_certificate,
        )
    return client


def connect_eventhub_client():
    """
    connect the module client for the EventHub implementation we're using return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.EventHubClient()
    client.connect(current_config.eventhub.connection_string)
    return client


def connect_registry_client():
    """
    connect the module client for the Registry implementation we're using return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.RegistryClient()
    client.connect(current_config.registry.connection_string)
    return client


def connect_service_client():
    """
    connect the module client for the ServiceClient implementation we're using return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.ServiceClient()
    client.connect(current_config.service.connection_string)
    return client


def connect_leaf_device_client():
    """
    connect the device client for the leaf device and return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.LeafDeviceClient()
    client.connect(
        current_config.leaf_device.transport,
        current_config.leaf_device.connection_string,
        current_config.ca_certificate,
    )
    return client


def connect_test_device_client():
    """
    connect the device client for the test device and return the client object
    """
    current_config = runtime_config.get_current_config()
    client = adapters.TestDeviceClient()
    client.connect(
        current_config.test_device.transport,
        current_config.test_device.connection_string,
        current_config.ca_certificate,
    )
    return client
