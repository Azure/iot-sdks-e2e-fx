# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import asyncio
import json
import ast
import random
import datetime
import threading
from threading import Event
from azure.eventhub.aio import EventHubConsumerClient
from ..adapter_config import logger
from . import eventhub_connection_string

object_list = []


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
        self.listener_complete = None

    def create_from_connection_string_sync(self, connection_string):
        self.iothub_connection_string = connection_string
        self.eventhub_connection_string = eventhub_connection_string.convert_iothub_to_eventhub_conn_str(
            connection_string
        )

    async def connect(self, offset=None):
        logger(
            "connect: thread={} {} loop={}".format(
                threading.current_thread(),
                id(threading.current_thread()),
                id(asyncio.get_running_loop()),
            )
        )
        if not offset:
            offset = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)

        global object_list
        if self not in object_list:
            object_list.append(self)

        self.received_events = asyncio.Queue()

        # Create a consumer client for the event hub.
        self.consumer_client = EventHubConsumerClient.from_connection_string(
            self.eventhub_connection_string, consumer_group="$Default"
        )

        async def on_event(partition_context, event):
            logger("received {}".format(event))
            await self.received_events.put(event)

        self.listener_complete = Event()

        async def listener():
            try:
                await self.consumer_client.receive(on_event, starting_position=offset)
            finally:
                self.listener_complete.set()

        self.listener_future = asyncio.ensure_future(listener())

    async def _close_eventhub_client(self):

        logger(
            "close: thread={} {} loop={}".format(
                threading.current_thread(),
                id(threading.current_thread()),
                id(asyncio.get_running_loop()),
            )
        )

        if self.consumer_client:
            logger("_close_eventhub_client: stopping consumer client")
            await self.consumer_client.close()
            logger("_close_eventhub_client: done stopping consumer client")
            self.consumer_client = None

        if self.listener_future:
            logger("_close_eventhub_client: cancelling listener")
            self.listener_future.cancel()
            logger("_close_eventhub_client: waiting for listener to complete")
            await self.listener_future
            self.listener_complete.wait()
            logger("_close_eventhub_client: listener is complete")
            self.listener_complete = None

    async def disconnect(self):
        logger("async disconnect {}".format(object_list))
        if self in object_list:
            object_list.remove(self)
            await self._close_eventhub_client()

    async def wait_for_next_event(self, device_id, expected=None):
        logger("EventHubApi: waiting for next event for {}".format(device_id))

        while True:
            event = await self.received_events.get()
            if get_device_id_from_event(event) == device_id:
                logger("EventHubApi: received event: {}".format(event.body_as_str()))
                received = event.body_as_json()
                if expected is not None:
                    if json_is_same(expected, received):
                        logger("EventHubApi: message received as expected")
                        return received
                    else:
                        logger("EventHubApi: unexpected message.  skipping")
                else:
                    return received
