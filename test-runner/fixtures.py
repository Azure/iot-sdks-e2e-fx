# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import pytest_asyncio
from connections import get_adapter, create_client, cleanup_adapter
import sample_content
from horton_settings import settings
from horton_logging import logger

try:
    async_fixture = pytest_asyncio.fixture
except AttributeError:
    async_fixture = pytest.fixture


@async_fixture
async def eventhub(event_loop):
    # we need the event_loop fixture so pytest_async creates the event loop before celling this.
    # Otherwise we get errors realted to mis-matched event loops when cleaning up this object.
    obj = settings.eventhub
    try:
        yield await get_adapter(obj)
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def registry():
    obj = settings.registry
    try:
        yield await get_adapter(obj)
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def service():
    obj = settings.service
    try:
        yield await get_adapter(obj)
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def friend():
    obj = settings.friend_module

    if obj.device_id and obj.module_id:
        adapter = await get_adapter(obj)
        await create_client(obj)
    else:
        adapter = None

    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def test_module():
    obj = settings.test_module

    if obj.device_id and obj.module_id:
        adapter = await get_adapter(obj)
        await create_client(obj)
    else:
        adapter = None

    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def leaf_device():
    obj = settings.leaf_device

    if obj.device_id:
        adapter = await get_adapter(obj)
        await create_client(obj)
    else:
        adapter = None

    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def test_device():
    obj = settings.test_device

    if obj.device_id:
        adapter = await get_adapter(obj)
        await create_client(obj)
    else:
        adapter = None

    try:
        yield adapter
    finally:
        await cleanup_adapter(obj)


@async_fixture
async def system_control():
    adapter = getattr(settings.system_control, "adapter", None)
    try:
        yield adapter
    finally:
        if adapter:
            logger("system_control finalizer".center(132, "-"))
            await adapter.reconnect_network()


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
