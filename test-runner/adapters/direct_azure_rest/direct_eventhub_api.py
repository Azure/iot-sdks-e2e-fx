#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
import json
import ast
from azure.eventhub import EventHubClient
from azure.eventhub.common import Offset
from azure.eventhub.common import EventHubError
from ..print_message import print_message

# our receive loop cycles through our 4 partitions, waiting for
# RECEIVE_CYCLE_TIME seconds at each partition for a message to arrive
RECEIVE_CYCLE_TIME = 0.25

object_list = []


def json_is_same(a, b):
    # If either parameter is a string, convert it to an object.
    # use ast.literal_eval because they might be single-quote delimited which fails with json.loads.
    if isinstance(a, str):
        a = ast.literal_eval(a)
    if isinstance(b, str):
        b = ast.literal_eval(b)
    return a == b


class EventHubApi:
    def __init__(self):
        global object_list
        self.client = None
        self.receivers = []
        object_list.append(self)

    def connect(self, connection_string):
        started = False
        while not started:
            print_message("EventHubApi: connecting EventHubClient")
            self.client = EventHubClient.from_iothub_connection_string(connection_string)
            print("EventHubApi: enabling EventHub telemetry")
            # partition_ids = self.client.get_eventhub_info()["partition_ids"]
            partition_ids = [0, 1, 2, 3]
            self.receivers = []
            for id in partition_ids:
                print_message("EventHubApi: adding receiver for partition {}".format(id))
                receiver = self.client.add_receiver(
                    "$default", id, operation="/messages/events", offset=Offset("@latest")
                )
                self.receivers.append(receiver)

            print_message("EventHubApi: starting client")

            try:
                self.client.run()
                started = True
            except EventHubError as e:
                if e.message.startswith("ErrorCodes.ResourceLimitExceeded"):
                    print("eventhub ResourceLimitExceeded.  Sleeping and trying again")
                    self.client.stop()
                    self.client = None
                    time.sleep(20)
                else:
                    raise e
                
            print_message("EventHubApi: ready")

    def disconnect(self):
        if self in object_list:
            object_list.remove(self)
        if self.client:
            self.client.stop()
            self.client = None

    def wait_for_next_event(self, device_id, timeout, expected=None):
        print_message("EventHubApi: waiting for next event for {}".format(device_id))
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            for receiver in self.receivers:
                batch = receiver.receive(max_batch_size=1, timeout=RECEIVE_CYCLE_TIME)
                if batch and (batch[0].device_id.decode("ascii") == device_id):
                    print_message(
                        "EventHubApi: received event: {}".format(batch[0].body_as_str())
                    )
                    received = batch[0].body_as_json()
                    if expected:
                        if json_is_same(expected, received):
                            print_message("EventHubApi: message received as expected")
                            return received
                        else:
                            print_message("EventHubApi: unexpected message.  skipping")
                    else:
                        return received
