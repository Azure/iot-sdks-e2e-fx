# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import asyncio
import ast
import datetime
import threading
from pprint import pprint
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
        self.starting_position = None

    async def create_from_connection_string(self, connection_string):
        self.iothub_connection_string = connection_string
        self.eventhub_connection_string = eventhub_connection_string.convert_iothub_to_eventhub_conn_str(
            connection_string
        )

    async def connect(self, starting_position=None):
        logger(
            "EventHubApi: connect: thread={} {} loop={}".format(
                threading.current_thread(),
                id(threading.current_thread()),
                id(asyncio.get_running_loop()),
            )
        )
        self.starting_position = starting_position or (
            datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        )
        self.received_events = asyncio.Queue()

        # Create a consumer client for the event hub.
        self.consumer_client = EventHubConsumerClient.from_connection_string(
            self.eventhub_connection_string, consumer_group="$Default"
        )

        await self.start_new_listener()

    async def start_new_listener(self):

        if self.listener_future:
            logger("EventHubApi: cancelling old listener")
            self.listener_future.cancel()
            try:
                await self.listener_future
            except asyncio.CancelledError:
                pass
            self.listener_future = None

        async def on_event(partition_context, event):
            # this receives all events.  they get filtered by device_id (if necessary) when
            # pulled from the queue
            await self.received_events.put(event)
            await partition_context.update_checkpoint(event)
            self.starting_position[partition_context.partition_id] = event.offset
            logger(
                "EventHubApi: partition {} at context {}".format(
                    partition_context.partition_id, event.offset
                )
            )

        async def on_error(partition_context, error):
            # Put your code here. partition_context can be None in the on_error callback.
            if partition_context:
                logger(
                    "EventHubApi: An exception: {} occurred during receiving from Partition: {}.".format(
                        partition_context.partition_id, error
                    )
                )
            else:
                logger(
                    "EventHubApi: An exception: {} occurred during the load balance process.".format(
                        error
                    )
                )

        async def on_partition_initialize(partition_context):
            # Put your code here.
            logger(
                "EventHubApi: Partition: {} has been initialized.".format(
                    partition_context.partition_id
                )
            )

        async def on_partition_close(partition_context, reason):
            # Put your code here.
            logger(
                "EventHubApi: Partition: {} has been closed, reason for closing: {}.".format(
                    partition_context.partition_id, reason
                )
            )

        async def get_current_position():
            positions = {}
            ids = await self.consumer_client.get_partition_ids()
            for id in ids:
                properties = await self.consumer_client.get_partition_properties(id)
                positions[id] = properties.get("last_enqueued_sequence_number") or "-1"
            return positions

        async def listener():
            try:
                if not self.starting_position:
                    # if we don't have a starting position, start at the current one and
                    # save it so we can update it as we receive events.
                    starting_position = await get_current_position()
                    self.starting_position = starting_position
                elif isinstance(self.starting_position, dict):
                    # if our starting position is a dict, use it and keep updating it as we
                    # receive events.
                    starting_position = self.starting_position
                else:
                    # if we do have a starting position, but it's not a dict, use it and get
                    # the current position so we can update it as events come in.
                    starting_position = self.starting_position
                    self.starting_position = await get_current_position()
                print("EventHubApi: listening at")
                pprint(self.starting_position)
                await self.consumer_client.receive(
                    on_event=on_event,
                    on_error=on_error,
                    starting_position=starting_position,
                    on_partition_initialize=on_partition_initialize,
                    on_partition_close=on_partition_close,
                )
            except Exception as e:
                logger("EventHubApi exception: {}".format(e))
                raise

        def done_cb(*args, **kwargs):
            logger("** listener future is done")
            logger("cancelled? {}".format(self.listener_future.cancelled()))
            logger(
                "exception {} {} ".format(
                    self.listener_future.exception(),
                    type(self.listener_future.exception()),
                )
            )

        self.listener_future = asyncio.ensure_future(listener())
        self.listener_future.add_done_callback(done_cb)

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
