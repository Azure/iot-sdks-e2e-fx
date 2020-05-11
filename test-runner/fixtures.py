# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import connections
import adapters
import json
import utilities
import sample_content
from adapters import adapter_config
from horton_settings import settings
from horton_logging import logger


def separator(message=""):
    return message.center(132, "-")


@pytest.fixture
async def eventhub(event_loop):
    eventhub = adapters.create_adapter(settings.eventhub.adapter_address, "eventhub")
    await eventhub.create_from_connection_string(settings.eventhub.connection_string)
    try:
        yield eventhub
    finally:
        logger(separator("eventhub finalizer"))
        try:
            await eventhub.disconnect()
        except Exception as e:
            logger("exception disconnecting eventhub: {}".format(e))


@pytest.fixture
async def registry():
    registry = await connections.connect_registry_client()
    try:
        yield registry
    finally:
        logger(separator("registry finalizer"))
        try:
            await registry.disconnect()
        except Exception as e:
            logger("exception disconnecting registry: {}".format(e))


@pytest.fixture
async def friend():
    if settings.friend_module.adapter_address:
        friend_module = await connections.get_module_client(settings.friend_module)
        try:
            yield friend_module
        finally:
            logger(separator("friend finalizer"))
            try:
                if friend_module.capabilities.v2_connect_group:
                    await friend_module.destroy()
                else:
                    await friend_module.disconnect()
            except Exception as e:
                logger("exception disconnecting friend module: {}".format(e))
    else:
        yield None


@pytest.fixture
async def test_module():
    test_module = await connections.get_module_client(settings.test_module)
    try:
        yield test_module
    finally:
        logger(separator("module finalizer"))
        try:
            if test_module.capabilities.v2_connect_group:
                await test_module.destroy()
            else:
                await test_module.disconnect()
        except Exception as e:
            logger("exception disconnecting test module: {}".format(e))


@pytest.fixture
async def leaf_device():
    if settings.leaf_device.adapter_address:
        leaf_device = await connections.get_device_client(settings.leaf_device)
        try:
            yield leaf_device
        finally:
            logger(separator("leaf_device finalizer"))
            try:
                if leaf_device.capabilities.v2_connect_group:
                    await leaf_device.destroy()
                else:
                    await leaf_device.disconnect()
            except Exception as e:
                logger("exception disconnecting leaf device: {}".format(e))
    else:
        yield None


@pytest.fixture
async def test_device():
    test_device = await connections.get_device_client(settings.test_device)
    try:
        yield test_device
    finally:
        logger(separator("test_device finalizer"))
        try:
            if test_device.capabilities.v2_connect_group:
                await test_device.destroy()
            else:
                await test_device.disconnect()
        except Exception as e:
            logger("exception disconnecting test device: {}".format(e))


@pytest.fixture
async def service():
    service = await connections.connect_service_client()
    try:
        yield service
    finally:
        logger(separator("service finalizer"))
        try:
            await service.disconnect()
        except Exception as e:
            logger("exception disconnecting service: {}".format(e))


@pytest.fixture
async def net_control():
    api = getattr(settings.net_control, "api", None)
    try:
        yield api
    finally:
        if api:
            logger(separator("net_control finalizer"))
            await settings.net_control.api.reconnect()


@pytest.fixture(
    scope="function",
    params=[
        pytest.param({}, id="empty object"),
        pytest.param(sample_content.make_message_payload(1), id="smallest object"),
        pytest.param(sample_content.make_message_payload(40), id="small object"),
        pytest.param(sample_content.make_message_payload(63 * 1024), id="63K object"),
        pytest.param(sample_content.make_message_payload(127 * 1024), id="127K object"),
        pytest.param(sample_content.make_message_payload(255 * 1024), id="255K object"),
    ],
)
def telemetry_payload(request):
    return request.param
