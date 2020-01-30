# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
from horton_settings import settings

all_langauges = ["pythonv2", "c", "csharp", "java", "node"]


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


def uses_shared_key_auth(client):
    """
    return True if the client supports shared key auth
    """
    return client.settings.connection_type.startswith("connection_string")


def only_run_test_for(client, languages):
    """
    only run the test for the given language(s)
    """
    if isinstance(languages, str):
        languages = (languages,)
    for language in languages:
        if language not in all_langauges:
            raise ValueError("Language {} is invalid".format(language))
        if client.settings.language == language:
            return
    pytest.skip()


def skip_test_for(client, languages):
    """
    skip the test for the given language(s)
    """
    if isinstance(languages, str):
        languages = (languages,)
    for language in languages:
        if language not in all_langauges:
            raise ValueError("Language {} is invalid".format(language))
        if client.settings.language == language:
            pytest.skip()


def skip_if_no_net_control():
    """
    Skip the test if we don't have a net_control API
    """
    if not settings.net_control.adapter_address:
        pytest.skip()


def only_run_test_on_iotedge_module(client):
    if client.settings.object_type != "iotedge_module":
        pytest.skip()
