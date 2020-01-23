# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
import base64
from horton_settings import settings


def get_ca_cert(settings_object):
    if (
        settings_object.connection_type == "connection_string_with_edge_gateway"
        and settings.iotedge.ca_cert_base64
    ):
        return {
            "cert": base64.b64decode(settings.iotedge.ca_cert_base64).decode("utf-8")
        }
    else:
        return {}


def get_module_client(settings_object):
    """
    get a module client for the given settings object
    """
    client = adapters.create_adapter(settings_object.adapter_address, "module_client")

    client.device_id = settings_object.device_id
    client.module_id = settings_object.module_id
    client.capabilities = settings_object.capabilities
    client.settings = settings_object

    if settings_object.capabilities.v2_connect_group:
        if settings_object.connection_type == "environment":
            client.create_from_environment_sync(settings_object.transport)
        else:
            client.create_from_connection_string_sync(
                settings_object.transport,
                settings_object.connection_string,
                get_ca_cert(settings_object),
            )
    else:
        if settings_object.connection_type == "environment":
            client.connect_from_environment_sync(settings_object.transport)
        else:
            client.connect_sync(
                settings_object.transport,
                settings_object.connection_string,
                get_ca_cert(settings_object),
            )
    return client


def get_device_client(settings_object):
    """
    get a device client for the given settings object
    """
    client = adapters.create_adapter(settings_object.adapter_address, "device_client")

    client.device_id = settings_object.device_id
    client.capabilities = settings_object.capabilities
    client.settings = settings_object

    if settings_object.capabilities.v2_connect_group:
        client.create_from_connection_string_sync(
            settings_object.transport,
            settings_object.connection_string,
            get_ca_cert(settings_object),
        )
    else:
        client.connect_sync(
            settings_object.transport,
            settings_object.connection_string,
            get_ca_cert(settings_object),
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


def get_net_control_api():
    """
    return an object that can be used to control the network
    """
    api = adapters.create_adapter(settings.net_control.adapter_address, "net")
    api.set_destination_sync(
        settings.net_control.test_destination, settings.test_module.transport
    )
    return api
