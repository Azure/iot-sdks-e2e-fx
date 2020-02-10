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


@pytest.fixture
def eventhub():
    eventhub = adapters.create_adapter(settings.eventhub.adapter_address, "eventhub")
    eventhub.create_from_connection_string_sync(settings.eventhub.connection_string)
    return eventhub


@pytest.fixture
def registry():
    registry = connections.connect_registry_client()
    return registry


@pytest.fixture
def friend():
    friend = connections.get_module_client(settings.friend_module)
    return friend


@pytest.fixture
def test_module():
    test_module = connections.get_module_client(settings.test_module)
    return test_module


@pytest.fixture
def leaf_device():
    leaf_device = connections.get_device_client(settings.leaf_device)
    return leaf_device


@pytest.fixture
def test_device():
    test_device = connections.get_device_client(settings.test_device)
    return test_device


@pytest.fixture
def service():
    service = connections.connect_service_client()
    return service


@pytest.fixture
def net_control():
    api = getattr(settings.net_control, "api", None)
    yield api
    if api:
        dashes = "".join(("-" for _ in range(0, 30)))
        separator = "{} CLEANUP {} {}".format(dashes, "{}", dashes)
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
