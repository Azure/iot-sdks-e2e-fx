# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest
import json
from horton_settings import settings


class TelemetryTests(object):
    @pytest.mark.it("Can send telemetry directly to IoTHub")
    async def test_send_telemetry_to_iothub(
        self, client, eventhub, telemetry_payload, logger, request
    ):
        if (
            len(str(telemetry_payload)) > 65500
            and settings.horton.transport == "amqpws"
            and settings.horton.language == "java"
        ):
            pytest.skip("amqpws on Java can't do 64kb telemetry")

        await eventhub.connect()

        logger('sending "{}"'.format(telemetry_payload))

        await client.send_event(telemetry_payload)

        received_message = await eventhub.wait_for_next_event(
            client.device_id, expected=telemetry_payload
        )
        assert received_message is not None, "Message not received"

    @pytest.mark.it("Can send 5 telemetry events directly to iothub")
    async def test_send_5_telemetry_events_to_iothub(
        self, client, eventhub, sample_payload, logger
    ):
        payloads = [sample_payload() for x in range(0, 5)]
        futures = []

        # start listening before we send
        await eventhub.connect()
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id)
        )

        for payload in payloads:
            futures.append(asyncio.ensure_future(client.send_event(payload)))

        # wait for the send to complete, and verify that it arrvies
        await asyncio.gather(*futures)

        logger("All messages sent.  Awaiting reception")

        while len(payloads):
            received_message = await received_message_future

            if received_message in payloads:
                logger(
                    "Received expected message: {}, removing from list".format(
                        received_message
                    )
                )
                payloads.remove(received_message)
            else:
                logger("Received unexpected message: {}".format(received_message))

            if len(payloads):
                received_message_future = asyncio.ensure_future(
                    eventhub.wait_for_next_event(client.device_id)
                )
