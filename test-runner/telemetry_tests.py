# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import json
from models import HubEvent
import sample_content


class TelemetryTests(object):
    @pytest.mark.it("Can send telemetry directly to IoTHub")
    @pytest.mark.timeout(
        timeout=180
    )  # extra timeout in case eventhub needs to retry due to resource error
    async def test_send_telemetry_to_iothub(
        self, client, eventhub, test_object_stringified
    ):
        await client.send_event(test_object_stringified)

        received_message = await eventhub.wait_for_next_event(
            client.device_id, expected=test_object_stringified
        )
        assert received_message is not None, "Message not received"

    @pytest.mark.parametrize("body", sample_content.telemetry_test_objects)
    @pytest.mark.uses_new_message_format
    @pytest.mark.timeout(
        timeout=180
    )  # extra timeout in case eventhub needs to retry due to resource error
    @pytest.mark.it(
        "Can send telemetry directly to IoTHub using the new Horton HubEvent"
    )
    async def test_device_send_telemetry_using_new_message_format(
        self, client, eventhub, body
    ):
        sent_message = HubEvent(body)
        await client.send_event(sent_message.convert_to_json())

        received_message = await eventhub.wait_for_next_event(
            client.device_id, expected=sent_message.body
        )
        assert received_message is not None, "Message not received"
