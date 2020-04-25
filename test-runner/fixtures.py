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

dashes = "".join(("-" for _ in range(0, 30)))
separator = "{} FINAL CLEANUP {} {}".format(dashes, "{}", dashes)


@pytest.fixture
async def eventhub(event_loop):
    eventhub = adapters.create_adapter(settings.eventhub.adapter_address, "eventhub")
    eventhub.create_from_connection_string_sync(settings.eventhub.connection_string)
    yield eventhub
    logger(separator.format("eventhub"))
    try:
        await eventhub.disconnect()
    except Exception as e:
        logger("exception disconnecting eventhub: {}".format(e))


@pytest.fixture
def registry():
    registry = connections.connect_registry_client()
    yield registry
    logger(separator.format("registry"))
    try:
        registry.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting registry: {}".format(e))


@pytest.fixture
def friend():
    if settings.friend_module.adapter_address:
        friend_module = connections.get_module_client(settings.friend_module)
        yield friend_module
        logger(separator.format("friend module"))
        try:
            friend_module.disconnect_sync()
        except Exception as e:
            logger("exception disconnecting friend module: {}".format(e))
    else:
        yield None


@pytest.fixture
def test_module():
    test_module = connections.get_module_client(settings.test_module)
    yield test_module
    logger(separator.format("test module"))
    try:
        test_module.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting test module: {}".format(e))


@pytest.fixture
def leaf_device():
    if settings.leaf_device.adapter_address:
        leaf_device = connections.get_device_client(settings.leaf_device)
        yield leaf_device
        logger(separator.format("leaf device"))
        try:
            leaf_device.disconnect_sync()
        except Exception as e:
            logger("exception disconnecting leaf device: {}".format(e))
    else:
        yield None


@pytest.fixture
def test_device():
    test_device = connections.get_device_client(settings.test_device)
    yield test_device
    logger(separator.format("device"))
    try:
        test_device.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting test device: {}".format(e))


@pytest.fixture
def service():
    service = connections.connect_service_client()
    yield service
    logger(separator.format("service"))
    try:
        service.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting service: {}".format(e))


@pytest.fixture
def net_control():
    api = getattr(settings.net_control, "api", None)
    yield api
    if api:
        logger(separator.format("net_control"))
        settings.net_control.api.reconnect_sync()


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
