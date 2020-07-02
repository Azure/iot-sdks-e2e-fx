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


async def _get_module_client(settings_object):
    """
    get a module client for the given settings object
    """
    client = adapters.create_adapter(settings_object.adapter_address, "module_client")

    client.device_id = settings_object.device_id
    client.module_id = settings_object.module_id
    client.capabilities = settings_object.capabilities
    client.settings = settings_object
    client.settings.client = client

    if settings_object.capabilities.v2_connect_group:
        if settings_object.connection_type == "environment":
            await client.create_from_environment(settings_object.transport)
        else:
            await client.create_from_connection_string(
                settings_object.transport,
                settings_object.connection_string,
                get_ca_cert(settings_object),
            )
    else:
        if settings_object.connection_type == "environment":
            await client.connect_from_environment(settings_object.transport)
        else:
            await client.connect(
                settings_object.transport,
                settings_object.connection_string,
                get_ca_cert(settings_object),
            )
    return client


async def _get_device_client(settings_object):
    """
    get a device client for the given settings object
    """
    client = adapters.create_adapter(settings_object.adapter_address, "device_client")

    client.device_id = settings_object.device_id
    client.capabilities = settings_object.capabilities
    client.settings = settings_object
    client.settings.client = client

    if settings_object.capabilities.v2_connect_group:
        await client.create_from_connection_string(
            settings_object.transport,
            settings_object.connection_string,
            get_ca_cert(settings_object),
        )
    else:
        await client.connect(
            settings_object.transport,
            settings_object.connection_string,
            get_ca_cert(settings_object),
        )
    return client


async def _get_eventhub_client():
    """
    get an eventhub client that we can use to watch telemetry operations
    """
    client = adapters.create_adapter(settings.eventhub.adapter_address, "eventhub")
    await client.create_from_connection_string(settings.eventhub.connection_string)
    client.settings = settings.eventhub
    client.settings.client = client
    return client


async def _get_registry_client():
    """
    connect the module client for the Registry implementation we're using return the client object
    """
    client = adapters.create_adapter(settings.registry.adapter_address, "registry")
    await client.connect(settings.registry.connection_string)
    client.settings = settings.registry
    client.settings.client = client
    return client


async def _get_service_client():
    """
    connect the module client for the ServiceClient implementation we're using return the client object
    """
    client = adapters.create_adapter(settings.service.adapter_address, "service")
    await client.connect(settings.service.connection_string)
    client.settings = settings.service
    client.settings.client = client
    return client


async def get_net_control_api():
    """
    return an object that can be used to control the network
    """
    api = adapters.create_adapter(settings.net_control.adapter_address, "net")
    await api.set_destination(
        settings.net_control.test_destination, settings.test_module.transport
    )
    return api


async def get_client(settings_object):
    """
    get a client object for the givving settings object
    """
    if settings_object.object_type in ["iothub_device", "leaf_device"]:
        return await _get_device_client(settings_object)
    elif settings_object.object_type in ["iothub_module", "iotedge_module"]:
        return await _get_module_client(settings_object)
    elif settings_object.object_type == "iothub_registry":
        return await _get_registry_client()
    elif settings_object.object_type == "iothub_service":
        return await _get_service_client()
    elif settings_object.object_type == "eventhub":
        return await _get_eventhub_client()
    else:
        assert "invalid object_type: {}".format(settings_object.object_type)
