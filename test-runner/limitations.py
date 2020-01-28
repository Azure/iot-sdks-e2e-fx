# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


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
