# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
from connections import get_adapter, create_client, cleanup_adapter
import sample_content
from horton_settings import settings
from horton_logging import logger


@pytest.fixture
async def eventhub(event_loop):
    # we need the event_loop fixture so pytest_async creates the event loop before celling this.
    # Otherwise we get errors realted to mis-matched event loops when cleaning up this object.
    obj = settings.eventhub
    try:
        yield await get_adapter(obj)
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def registry():
    obj = settings.registry
    try:
        yield await get_adapter(obj)
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def service():
    obj = settings.service
    try:
        yield await get_adapter(obj)
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def friend():
    obj = settings.friend_module
    adapter = await get_adapter(obj)
    await create_client(obj)
    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def test_module():
    obj = settings.test_module
    adapter = await get_adapter(obj)
    await create_client(obj)
    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def leaf_device():
    obj = settings.leaf_device
    adapter = await get_adapter(obj)
    await create_client(obj)
    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def test_device(device_provisioning):
    obj = settings.test_device
    adapter = await get_adapter(obj)
    await create_client(obj, device_provisioning)
    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def longhaul_control_device(device_provisioning):
    obj = settings.longhaul_control_device
    adapter = await get_adapter(obj)
    await create_client(obj, device_provisioning)
    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def device_provisioning():
    obj = settings.device_provisioning
    adapter = await get_adapter(obj)
    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@pytest.fixture
async def net_control():
    adapter = getattr(settings.net_control, "adapter", None)
    try:
        yield adapter
    finally:
        if adapter:
            logger("net_control finalizer".center(132, "-"))
            await adapter.reconnect()


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
