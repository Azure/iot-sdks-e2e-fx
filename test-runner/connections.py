# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
import base64
from horton_settings import settings


def get_ca_cert(object):
    if (
        object.connection_type == "connection_string_with_edge_gateway"
        and settings.iotedge.ca_cert_base64
    ):
        return {
            "cert": base64.b64decode(settings.iotedge.ca_cert_base64).decode("utf-8")
        }
    else:
        return {}


def connect_test_module_client():
    """
    connect the module client for the code-under-test and return the client object
    """
    client = adapters.create_adapter(
        settings.test_module.adapter_address, "module_client"
    )

    client.device_id = settings.test_module.device_id
    client.module_id = settings.test_module.module_id

    if settings.test_module.connection_type == "environment":
        client.connect_from_environment_sync(settings.test_module.transport)
    else:
        client.connect_sync(
            settings.test_module.transport,
            settings.test_module.connection_string,
            get_ca_cert(settings.test_module),
        )
    return client


def connect_friend_module_client():
    """
    connect the module client for the friend module and return the client object
    """
    client = adapters.create_adapter(
        settings.friend_module.adapter_address, "module_client"
    )

    client.device_id = settings.friend_module.device_id
    client.module_id = settings.friend_module.module_id

    if settings.friend_module.connection_type == "environment":
        client.connect_from_environment_sync(settings.friend_module.transport)
    else:
        client.connect_sync(
            settings.friend_module.transport,
            settings.friend_module.connection_string,
            get_ca_cert(settings.friend_module),
        )
    return client


def connect_registry_client():
    """
    connect the module client for the Registry implementation we're using return the client object
    """
    client = adapters.create_adapter(settings.registry.adapter_address, "registry")
    client.connect_sync(settings.registry.connection_string)
    return client


def connect_service_client():
    """
    connect the module client for the ServiceClient implementation we're using return the client object
    """
    client = adapters.create_adapter(settings.service.adapter_address, "service")
    client.connect_sync(settings.service.connection_string)
    return client


def connect_leaf_device_client():
    """
    connect the device client for the leaf device and return the client object
    """
    client = adapters.create_adapter(
        settings.leaf_device.adapter_address, "device_client"
    )

    client.device_id = settings.leaf_device.device_id

    client.connect_sync(
        settings.leaf_device.transport,
        settings.leaf_device.connection_string,
        get_ca_cert(settings.leaf_device),
    )
    return client


def connect_test_device_client():
    """
    connect the device client for the test device and return the client object
    """
    client = adapters.create_adapter(
        settings.test_device.adapter_address, "device_client"
    )

    client.device_id = settings.test_device.device_id

    client.connect_sync(
        settings.test_device.transport, settings.test_device.connection_string, {}
    )
    return client
