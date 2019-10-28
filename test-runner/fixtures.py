# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import connections
from adapters import print_message
import runtime_config
from runtime_config import get_current_config
from utilities import random_string
from sample_content import next_random_string

# TODO: replace test content fixtures with generator fixtures
# TODO: remove test_ prefix on non-test functions


@pytest.fixture
def test_string():
    return random_string("String1")


@pytest.fixture
def test_string_2():
    return random_string("String2")


@pytest.fixture
def test_payload(test_string):
    return '{ "message": "' + test_string + '" }'


@pytest.fixture
def test_object_stringified(test_string):
    return '{ "message": "' + test_string + '" }'


@pytest.fixture
def test_object_stringified_2(test_string_2):
    return '{ "message": "' + test_string_2 + '" }'


@pytest.fixture(scope="session")
def logger():
    return print_message


dashes = "".join(("-" for _ in range(0, 30)))
separator = "{} CLEANUP {} {}".format(dashes, "{}", dashes)


@pytest.fixture
def eventhub(logger):
    eventhub = connections.connect_eventhub_client()
    yield eventhub
    logger(separator.format("eventhub"))
    eventhub.disconnect_sync()


@pytest.fixture
def registry(logger):
    registry = connections.connect_registry_client()
    yield registry
    logger(separator.format("registry"))
    registry.disconnect_sync()


@pytest.fixture
def friend(logger):
    friend = connections.connect_friend_module_client()
    friend.device_id = get_current_config().friend_module.device_id
    friend.module_id = get_current_config().friend_module.module_id
    yield friend
    logger(separator.format("friend module"))
    friend.disconnect_sync()


@pytest.fixture
def test_module(logger):
    test_module = connections.connect_test_module_client()
    test_module.device_id = get_current_config().test_module.device_id
    test_module.module_id = get_current_config().test_module.module_id
    yield test_module
    logger(separator.format("test module"))
    test_module.disconnect_sync()


@pytest.fixture
def leaf_device(logger):
    leaf_device = connections.connect_leaf_device_client()
    leaf_device.device_id = get_current_config().leaf_device.device_id
    yield leaf_device
    logger(separator.format("leaf device"))
    leaf_device.disconnect_sync()


@pytest.fixture
def test_device(logger):
    test_device = connections.connect_test_device_client()
    test_device.device_id = get_current_config().test_device.device_id
    yield test_device
    logger(separator.format("device"))
    test_device.disconnect_sync()


@pytest.fixture
def service(logger):
    service = connections.connect_service_client()
    yield service
    logger(separator.format("service"))
    service.disconnect_sync()


@pytest.fixture
def test_module_wrapper_api():
    return runtime_config.get_test_module_wrapper_api()


@pytest.fixture
def sample_reported_props():
    return lambda: {"foo": next_random_string("reported props")}


@pytest.fixture
def sample_desired_props():
    return lambda: {
        "properties": {"desired": {"foo": next_random_string("desired props")}}
    }


@pytest.fixture
def sample_payload():
    return lambda: next_random_string("payload")
