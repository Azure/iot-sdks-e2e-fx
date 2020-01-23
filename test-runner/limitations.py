# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


def get_maximum_telemetry_message_size(client):
    if client.settings.language == "java" and client.settings.transport == "amqpws":
        # java amqpws limitation
        return 63 * 1024
    elif client.settings.language == "node":
        # node swagger wrapper limitation
        return 64 * 1024
    else:
        return 255 * 1024


def can_always_overlap_telemetry_messages(client):
    if client.settings.language == "node":
        # node will fail test_send_5_telemetry_events_to_iothub 1/10 times
        return False
    else:
        return True
