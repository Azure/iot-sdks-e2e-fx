# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import json
from models import HubEvent


class TelemetryTests(object):
    @pytest.mark.it("Can send telemetry directly to IoTHub")
    @pytest.mark.timeout(
        timeout=180
    )  # extra timeout in case eventhub needs to retry due to resource error
    def test_send_event_to_iothub(
        self, logger, client, eventhub, test_object_stringified
    ):
        client.send_event(test_object_stringified)

        received_message = eventhub.wait_for_next_event(
            client.device_id, expected=test_object_stringified
        )
        if not received_message:
            logger("Message not received")
            assert False

    @pytest.mark.uses_new_message_format
    @pytest.mark.timeout(
        timeout=180
    )  # extra timeout in case eventhub needs to retry due to resource error
    @pytest.mark.it(
        "Can send telemetry directly to IoTHub using the new message format"
    )
    def test_device_send_string_using_new_message_format(
        self, logger, client, eventhub, test_string
    ):
        sent_message = HubEvent()
        sent_message.body = json.dumps(test_string)

        client.send_event(sent_message.convert_to_json())

        received_message = eventhub.wait_for_next_event(
            client.device_id, expected=sent_message.body
        )
        if not received_message:
            logger("Message not received")
            assert False
