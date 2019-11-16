# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import connections
import adapters
from adapters import adapter_config
from utilities import random_string
from sample_content import next_random_string
from horton_settings import settings

# BKTODO: replace test content fixtures with generator fixtures
# BKTODO: remove test_ prefix on non-test functions


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
    except e:
        logger("exception disconnecting eventhub: {}".format(e))


@pytest.fixture
def registry(logger):
    registry = connections.connect_registry_client()
    yield registry
    logger(separator.format("registry"))
    try:
        registry.disconnect_sync()
    except e:
        logger("exception disconnecting registry: {}".format(e))


@pytest.fixture
def friend(logger):
    friend = connections.connect_friend_module_client()
    yield friend
    logger(separator.format("friend module"))
    try:
        friend.disconnect_sync()
    except e:
        logger("exception disconnecting friend module: {}".format(e))


@pytest.fixture
def test_module(logger):
    test_module = connections.connect_test_module_client()
    yield test_module
    logger(separator.format("test module"))
    try:
        test_module.disconnect_sync()
    except e:
        logger("exception disconnecting test module: {}".format(e))


@pytest.fixture
def leaf_device(logger):
    leaf_device = connections.connect_leaf_device_client()
    yield leaf_device
    logger(separator.format("leaf device"))
    try:
        leaf_device.disconnect_sync()
    except e:
        logger("exception disconnecting leaf device: {}".format(e))


@pytest.fixture
def test_device(logger):
    test_device = connections.connect_test_device_client()
    yield test_device
    logger(separator.format("device"))
    try:
        test_device.disconnect_sync()
    except e:
        logger("exception disconnecting test device: {}".format(e))


@pytest.fixture
def service(logger):
    service = connections.connect_service_client()
    yield service
    logger(separator.format("service"))
    try:
        service.disconnect_sync()
    except e:
        logger("exception disconnecting service: {}".format(e))


@pytest.fixture
def test_module_wrapper_api():
    # BKTODO change the pattern to use the right name and right api
    return settings.test_module.wrapper_api


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
