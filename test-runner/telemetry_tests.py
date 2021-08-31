# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest
import json
import limitations
import sample_content
from horton_settings import settings
from horton_logging import logger


async def wait_for_all_telemetry_messages_to_arrive(
    *, received_message_future, payloads, eventhub, client
):
    """
    wait for a set of telemetry messages to arrive at eventhub
    """
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


def ensure_send_telemetry_message(*, client, payloads, send_futures):
    payload = sample_content.make_message_payload()
    payloads.append(payload)
    send_futures.append(asyncio.ensure_future(client.send_event(payload)))


class TelemetryTests(object):
    @pytest.mark.it("Can send telemetry directly to IoTHub")
    async def test_send_telemetry_to_iothub(self, client, eventhub, telemetry_payload):
        if len(str(telemetry_payload)) > limitations.get_maximum_telemetry_message_size(
            client
        ):
            pytest.skip("message is too big")

        await eventhub.connect()


    @pytest.mark.it("Can send 5 telemetry events directly to iothub")
    async def test_send_5_telemetry_events_to_iothub(self, client, eventhub):
        if not limitations.can_always_overlap_telemetry_messages(client):
            pytest.skip("client's can't reliably overlap telemetry messages")

        payloads = []
        send_futures = []

        # start listening before we send
        await eventhub.connect()
        received_message_future = asyncio.ensure_future(
            eventhub.wait_for_next_event(client.device_id)
        )

        for _ in range(0, 5):
            ensure_send_telemetry_message(
                client=client, payloads=payloads, send_futures=send_futures
            )

        # wait for the sends to complete, and verify that they arrive
        await asyncio.gather(*send_futures)

        logger("All messages sent.  Awaiting reception")
        await wait_for_all_telemetry_messages_to_arrive(
            received_message_future=received_message_future,
            payloads=payloads,
            eventhub=eventhub,
            client=client,
        )
