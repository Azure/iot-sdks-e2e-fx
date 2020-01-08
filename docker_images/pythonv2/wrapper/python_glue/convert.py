# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
import logging
from azure.iot.device import Message

logger = logging.getLogger(__name__)


def test_script_object_to_outgoing_message(payload):
    """
    Convert an object that we received from a test script into something that we
    can pass into the iothub sdk.
    """

    return Message(bytearray(json.dumps(payload.body), "utf-8"))


def incoming_message_to_test_script_object(message):
    """
    convert an object that we receive from IoTHub or EdgeHub into an object that
    our test scripts can understand
    """
    payload = message.data
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return {"body": json.loads(payload)}
