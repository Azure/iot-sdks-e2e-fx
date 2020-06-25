# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import asyncio
import ast
import datetime
import threading
from azure.eventhub.aio import EventHubConsumerClient
from ..adapter_config import logger
from . import eventhub_connection_string


def json_is_same(a, b):
    # If either parameter is a string, convert it to an object.
    # use ast.literal_eval because they might be single-quote delimited which fails with json.loads.
    # if ast.literal_eval raises a ValueError, leave it as a string -- it must not be json after all.
    if isinstance(a, str):
        try:
            a = ast.literal_eval(a)
        except (ValueError, SyntaxError):
            pass
    if isinstance(b, str):
        try:
            b = ast.literal_eval(b)
        except (ValueError, SyntaxError):
            pass
    return a == b


def get_device_id_from_event(event):
    return event.message.annotations["iothub-connection-device-id".encode()].decode()


class EventHubApi:
    def __init__(self):
        self.consumer_client = None
        self.iothub_connection_string = None
        self.eventhub_connection_string = None
        self.received_events = None
        self.listener_future = None

    async def create_from_connection_string(self, connection_string):
        self.iothub_connection_string = connection_string
        self.eventhub_connection_string = eventhub_connection_string.convert_iothub_to_eventhub_conn_str(
            connection_string
        )

    async def connect(self, offset=None):
        logger(
            "EventHubApi: connect: thread={} {} loop={}".format(
                threading.current_thread(),
                id(threading.current_thread()),
                id(asyncio.get_running_loop()),
            )
        )
        if not offset:
            offset = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)

        self.received_events = asyncio.Queue()

        # Create a consumer client for the event hub.
        self.consumer_client = EventHubConsumerClient.from_connection_string(
            self.eventhub_connection_string, consumer_group="$Default"
        )

        async def on_event(partition_context, event):
            # this receives all events.  they get filtered by device_id (if necessary) when
            # pulled from the queue
            await self.received_events.put(event)

        async def listener():
            await self.consumer_client.receive(on_event, starting_position=offset)

        self.listener_future = asyncio.ensure_future(listener())

        logger("EventHubApi: Listener Created")

    async def _close_eventhub_client(self):

        logger(
            "EventHubApi: close: thread={} {} loop={}".format(
                threading.current_thread(),
                id(threading.current_thread()),
                id(asyncio.get_running_loop()),
            )
        )

        if self.consumer_client:
            logger("EventHubApi: _close_eventhub_client: stopping consumer client")
            await self.consumer_client.close()
            logger("EventHubApi: _close_eventhub_client: done stopping consumer client")
            self.consumer_client = None

        if self.listener_future:
            logger("EventHubApi: _close_eventhub_client: cancelling listener")
            self.listener_future.cancel()
            logger(
                "EventHubApi: _close_eventhub_client: waiting for listener to complete"
            )
            try:
                await self.listener_future
            except asyncio.CancelledError:
                pass
            logger("_close_eventhub_client: listener is complete")

    async def disconnect(self):
        logger("EventHubApi: async disconnect")
        await self._close_eventhub_client()

    async def wait_for_next_event(self, device_id, expected=None):
        logger("EventHubApi: waiting for next event for {}".format(device_id))

        while True:
            event = await self.received_events.get()
            if not device_id:
                return event.body_as_json()
            elif get_device_id_from_event(event) == device_id:
                logger(
                    "EventHubApi: received event: {}".format(event.body_as_str()[:80])
                )
                received = event.body_as_json()
                if expected is not None:
                    if json_is_same(expected, received):
                        logger("EventHubApi: message received as expected")
                        return received
                    else:
                        logger("EventHubApi: unexpected message.  skipping")
                else:
                    return received
            else:
                logger("EventHubApi: event not for me received")
