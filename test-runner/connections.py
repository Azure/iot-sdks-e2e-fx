# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
import base64
import hmac
import hashlib
from horton_settings import settings
from horton_logging import logger


def separator(message=""):
    return message.center(132, "-")


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


async def _get_module_client_adapter(settings_object):
    """
    get a module client adapter for the given settings object
    """
    if not settings_object.device_id or not settings_object.module_id:
        return None

    adapter = adapters.create_adapter(settings_object.adapter_address, "module_client")

    adapter.device_id = settings_object.device_id
    adapter.module_id = settings_object.module_id

    return adapter


async def _get_device_client_adapter(settings_object):
    """
    get a device client adapter for the given settings object
    """
    if not settings_object.device_id and not settings_object.id_scope:
        return None

    adapter = adapters.create_adapter(settings_object.adapter_address, "device_client")

    adapter.device_id = settings_object.device_id

    return adapter


async def _get_device_provisioning_client_adapter(settings_object):
    """
    get a device client adapter for the given settings object
    """
    adapter = adapters.create_adapter(
        settings_object.adapter_address, "device_provisioning"
    )
    return adapter


async def _get_eventhub_client_adapter(settings_object):
    """
    get an eventhub client adapter that we can use to watch telemetry operations
    """
    adapter = adapters.create_adapter(settings_object.adapter_address, "eventhub")
    await adapter.create_from_connection_string(settings_object.connection_string)
    return adapter


async def _get_registry_client_adapter(settings_object):
    """
    connect the client adapter for the Registry implementation we're using
    """
    adapter = adapters.create_adapter(settings_object.adapter_address, "registry")
    await adapter.connect(settings_object.connection_string)
    return adapter


async def _get_service_client_adapter(settings_object):
    """
    connect the client for the ServiceClient implementation we're using return the client object
    """
    adapter = adapters.create_adapter(settings_object.adapter_address, "service")
    await adapter.connect(settings_object.connection_string)
    return adapter


async def _get_system_control_adapter(settings_object):
    """
    return an object that can be used to control the operating system
    """
    adapter = adapters.create_adapter(settings_object.adapter_address, "system_control")
    await adapter.set_network_destination(
        settings_object.test_destination, settings.test_module.transport
    )
    return adapter


async def get_adapter(settings_object):
    """
    get a client adapter object for the givving settings object
    """
    if not settings_object.adapter_address:
        return None
    elif settings_object.object_type in ["iothub_device", "leaf_device"]:
        adapter = await _get_device_client_adapter(settings_object)
    elif settings_object.object_type in ["iothub_module", "iotedge_module"]:
        adapter = await _get_module_client_adapter(settings_object)
    elif settings_object.object_type == "iothub_registry":
        adapter = await _get_registry_client_adapter(settings_object)
    elif settings_object.object_type == "iothub_service":
        adapter = await _get_service_client_adapter(settings_object)
    elif settings_object.object_type == "device_provisioning":
        adapter = await _get_device_provisioning_client_adapter(settings_object)
    elif settings_object.object_type == "eventhub":
        adapter = await _get_eventhub_client_adapter(settings_object)
    elif settings_object.object_type == "system_control":
        adapter = await _get_system_control_adapter(settings_object)
    else:
        assert "invalid object_type: {}".format(settings_object.object_type)

    adapter.capabilities = settings_object.capabilities
    adapter.settings = settings_object
    settings_object.adapter = adapter

    return adapter


def _derive_device_key(registration_id, group_symmetric_key):
    """
    The unique device ID and the group master key should be encoded into "utf-8"
    After this the encoded group master key must be used to compute an HMAC-SHA256 of the encoded registration ID.
    Finally the result must be converted into Base64 format.
    The device key is the "utf-8" decoding of the above result.
    """
    message = registration_id.encode("utf-8")
    signing_key = base64.b64decode(group_symmetric_key.encode("utf-8"))
    signed_hmac = hmac.HMAC(signing_key, message, hashlib.sha256)
    device_key_encoded = base64.b64encode(signed_hmac.digest())
    return device_key_encoded.decode("utf-8")


async def _create_client_using_dps(settings_object, device_provisioning):
    adapter = settings_object.adapter

    await device_provisioning.create_from_symmetric_key(
        transport="mqtt",
        provisioning_host=settings_object.provisioning_host_name,
        registration_id=settings_object.registration_id,
        id_scope=settings_object.id_scope,
        symmetric_key=settings_object.symmetric_key,
    )
    if settings_object.capability_model_id:
        await device_provisioning.set_provisioning_payload(
            {"iotcModelId": settings_object.capability_model_id}
        )

    result = await device_provisioning.register()
    await device_provisioning.destroy()

    if result.status != "assigned":
        raise Exception("Invalid rgistration status: {}".result.status)

    settings_object.device_id = result.device_id
    settings_object.iothub_host_name = result.assigned_hub
    adapter.device_id = settings_object.device_id

    await adapter.create_from_symmetric_key(
        settings_object.transport,
        hostname=settings_object.iothub_host_name,
        symmetric_key=settings_object.symmetric_key,
        device_id=settings_object.device_id,
    )


async def _create_client_using_dps_group(settings_object, device_provisioning):
    settings_object.symmetric_key = _derive_device_key(
        settings_object.registration_id, settings_object.group_symmetric_key
    )

    await _create_client_using_dps(settings_object, device_provisioning)


async def create_client(settings_object, device_provisioning=None):
    adapter = settings_object.adapter

    if settings_object.connection_type == "dps_symmetric_key_group":
        await _create_client_using_dps_group(settings_object, device_provisioning)

    if settings_object.connection_type == "dps_symmetric_key":
        await _create_client_using_dps(settings_object, device_provisioning)

    elif settings_object.connection_type == "symmetric_key":
        await adapter.create_from_symmetric_key(
            settings_object.transport,
            hostname=settings_object.iothub_host_name,
            symmetric_key=settings_object.symmetric_key,
            device_id=settings_object.device_id,
        )

    elif settings_object.capabilities.v2_connect_group:
        if settings_object.connection_type == "environment":
            await adapter.create_from_environment(settings_object.transport)
        elif settings_object.connection_type.startswith("connection_string"):
            await adapter.create_from_connection_string(
                settings_object.transport,
                settings_object.connection_string,
                get_ca_cert(settings_object),
            )
    else:
        if settings_object.connection_type == "environment":
            await adapter.connect_from_environment(settings_object.transport)
        elif settings_object.connection_type.startswith("connection_string"):
            await adapter.connect(
                settings_object.transport,
                settings_object.connection_string,
                get_ca_cert(settings_object),
            )


async def cleanup_adapter(settings_object):
    if settings_object.adapter:
        logger(separator("{} finalizer".format(settings_object.name)))
        try:
            if (
                hasattr(settings_object.adapter, "capabilities")
                and hasattr(settings_object.adapter.capabilities, "v2_connect_group")
                and settings_object.adapter.capabilities.v2_connect_group
            ):
                logger("Destroying")
                await settings_object.adapter.destroy()
            elif hasattr(settings_object.adapter, "disconnect"):
                logger("Disconnecting")
                await settings_object.adapter.disconnect()
            elif hasattr(settings_object.adapter, "destroy"):
                logger("Destroying")
                await settings_object.adapter.destroy()
            logger("done finalizing {}".format(settings_object.name))
        except Exception as e:
            logger(
                "exception disconnecting {} module: {}".format(settings_object.name, e)
            )
        finally:
            settings_object.adapter = None
