# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import connections
import sample_content
from horton_settings import settings
from horton_logging import logger


def separator(message=""):
    return message.center(132, "-")


async def get_client(settings_object):
    if settings_object.adapter_address:
        return await connections.get_client(settings_object)
    else:
        return None


async def cleanup_client(settings_object):
    if settings_object.client:
        logger(separator("{} finalizer".format(settings_object.name)))
        try:
            if (
                hasattr(settings_object.client, "capabilities")
                and settings_object.client.capabilities.v2_connect_group
            ):
                logger("Destroying")
                await settings_object.client.destroy()
            else:
                logger("Disconnecting")
                await settings_object.client.disconnect()
            logger("done finalizing {}".format(settings_object.name))
        except Exception as e:
            logger(
                "exception disconnecting {} module: {}".format(settings_object.name, e)
            )
        finally:
            settings_object.client = None


@pytest.fixture
async def eventhub(event_loop):
    # we need the event_loop fixture so pytest_async creates the event loop before celling this.
    # Otherwise we get errors realted to mis-matched event loops when cleaning up this object.
    obj = settings.eventhub
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def registry():
    obj = settings.registry
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def service():
    obj = settings.service
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def friend():
    obj = settings.friend_module
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def test_module():
    obj = settings.test_module
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def leaf_device():
    obj = settings.leaf_device
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def test_device():
    obj = settings.test_device
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


@pytest.fixture
async def longhaul_control_device():
    obj = settings.longhaul_control_device
    try:
        yield await get_client(obj)
    finally:
        await cleanup_client(obj)


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
