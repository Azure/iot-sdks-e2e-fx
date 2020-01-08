# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import connections
import adapters
import json
from adapters import adapter_config
from utilities import random_string, next_random_string
from horton_settings import settings

# BKTODO: replace test content fixtures with generator fixtures
# BKTODO: remove test_ prefix on non-test functions


@pytest.fixture
def test_payload(sample_payload):
    return sample_payload()


@pytest.fixture
def test_object_stringified():
    return '{ "message": "' + next_random_string("tos") + '" }'


@pytest.fixture
def test_object_stringified_2():
    return '{ "message": "' + next_random_string("tos2") + '" }'


@pytest.fixture(scope="session")
def logger():
    return adapter_config.logger


dashes = "".join(("-" for _ in range(0, 30)))
separator = "{} CLEANUP {} {}".format(dashes, "{}", dashes)


@pytest.fixture
def eventhub(logger):
    eventhub = adapters.create_adapter(settings.eventhub.adapter_address, "eventhub")
    eventhub.create_from_connection_string_sync(settings.eventhub.connection_string)
    yield eventhub
    logger(separator.format("eventhub"))
    try:
        eventhub.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting eventhub: {}".format(e))


@pytest.fixture
def registry(logger):
    registry = connections.connect_registry_client()
    yield registry
    logger(separator.format("registry"))
    try:
        registry.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting registry: {}".format(e))


@pytest.fixture
def friend(logger):
    friend = connections.get_module_client(settings.friend_module)
    yield friend
    logger(separator.format("friend module"))
    try:
        friend.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting friend module: {}".format(e))


@pytest.fixture
def test_module(logger):
    test_module = connections.get_module_client(settings.test_module)
    yield test_module
    logger(separator.format("test module"))
    try:
        test_module.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting test module: {}".format(e))


@pytest.fixture
def leaf_device(logger):
    leaf_device = connections.get_device_client(settings.leaf_device)
    yield leaf_device
    logger(separator.format("leaf device"))
    try:
        leaf_device.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting leaf device: {}".format(e))


@pytest.fixture
def test_device(logger):
    test_device = connections.get_device_client(settings.test_device)
    yield test_device
    logger(separator.format("device"))
    try:
        test_device.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting test device: {}".format(e))


@pytest.fixture
def service(logger):
    service = connections.connect_service_client()
    yield service
    logger(separator.format("service"))
    try:
        service.disconnect_sync()
    except Exception as e:
        logger("exception disconnecting service: {}".format(e))


@pytest.fixture
def sample_reported_props():
    return lambda: {"reported": {"foo": next_random_string("reported props")}}


@pytest.fixture
def sample_desired_props():
    return lambda: {"desired": {"foo": next_random_string("desired props")}}


zero_size_payload = {}
minimum_payload = {"a": {}}


def make_payload(size):
    wrapper_overhead = len(json.dumps(minimum_payload))
    if size == 0:
        return zero_size_payload
    elif size <= wrapper_overhead:
        return minimum_payload
    else:
        return {"payload": random_string(length=size - wrapper_overhead - 7)}


@pytest.fixture
def sample_payload():
    return lambda: {"payload": next_random_string("payload")}


@pytest.fixture
def net_control():
    return settings.net_control.api


@pytest.fixture(
    scope="function",
    params=[
        pytest.param({}, id="empty object"),
        pytest.param(make_payload(1), id="smallest object"),
        pytest.param(make_payload(20), id="small object"),
        pytest.param(make_payload(65535), id="64K object"),
    ],
)
def telemetry_payload(request):
    return request.param
