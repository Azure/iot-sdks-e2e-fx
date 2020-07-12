# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
from horton_settings import settings

all_languages = set(["pythonv2", "c", "csharp", "java", "node"])
all_transports = set(["amqp", "amqpws", "mqtt", "mqttws"])


def get_maximum_telemetry_message_size(client):
    """
    Returns the maximum message size (in bytes) the client can support
    """
    if client.settings.language == "java" and client.settings.transport == "amqpws":
        # java amqpws limitation.  Actual number is unknown.  This just blocks 63K+ tests.
        # The real limit is probably near an even number like 32K
        return 62 * 1024
    elif client.settings.language == "node":
        # node swagger wrapper limitation
        return 64 * 1024
    else:
        return 255 * 1024


def can_always_overlap_telemetry_messages(client):
    """
    Returns True if the client can reliably overlay telemetry messages
    """
    if client.settings.language == "node":
        # node will fail test_send_5_telemetry_events_to_iothub 1/10 times
        return False
    else:
        return True


def _verify_and_make_set(var, allowed_values):
    """
    Turn a string or a list into a set so we can use set operations
    """
    if isinstance(var, str):
        var = set([var])
    elif isinstance(var, list):
        var = set(var)
    elif isinstance(var, set):
        pass
    else:
        raise ValueError("invalid type")

    if (var & allowed_values) != var:
        raise ValueError("invalid value")

    return var


def uses_shared_key_auth(client):
    """
    return True if the client supports shared key auth
    """
    return client.settings.connection_type.startswith("connection_string")


def only_run_test_for(client, languages):
    """
    only run the test for the given language(s)
    """
    languages = _verify_and_make_set(languages, all_languages)

    if client.settings.language not in languages:
        pytest.skip()


def skip_test_for(client, languages, transports=all_transports):
    """
    skip the test for the given language(s)
    """
    languages = _verify_and_make_set(languages, all_languages)
    transports = _verify_and_make_set(transports, all_transports)

    if (
        client.settings.language in languages
        and client.settings.transport in transports
    ):
        pytest.skip()


def skip_if_no_net_control():
    """
    Skip the test if we don't have a net_control API
    """
    if not settings.net_control.adapter:
        pytest.skip()


def only_run_test_on_iotedge_module(client):
    if client.settings.object_type != "iotedge_module":
        pytest.skip()


def only_run_test_on_iothub_device(client):
    if client.settings.object_type != "iothub_device":
        pytest.skip()
