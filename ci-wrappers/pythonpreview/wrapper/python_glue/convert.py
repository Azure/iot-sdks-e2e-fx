#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json


def new_test_script_message_object_to_outgoing_message(obj):
    if obj["bodyType"] == "string":
        return obj["body"]
    else:
        assert False


"""
    if isinstance(body, bytes):
        return body.decode("utf-8")
    else:
        return json.dumps(body)
"""


def test_script_object_to_outgoing_message(body):
    """
    Convert an object that we received from a test script into something that we
    can pass into the iothub sdk.
    """

    # if we're starting with bytes, convert it into a string, and then try to
    # deserialize it into an object.  This happens if we're calling into the
    # glue over REST.  If, however, we're calling into the glue directly, then
    # we skip this code.
    if isinstance(body, bytes):
        print("body is bytes.  decoding")
        body = body.decode("utf-8")
        try:
            body = json.loads(body)
            print("successfully deserialized")
        except json.decoder.JSONDecodeError:
            print("failed deserialization")
            pass

    # at this point, we should have a dict or a string.
    print("body is {}".format(body.__class__))
    if isinstance(body, dict):
        if "bodyType" in body:
            print("new object")
            # If we have a dict with a bodyType member, then it's a HubEvent object.
            return new_test_script_message_object_to_outgoing_message(body)
        else:
            print("stringify dictionary")
            # dict without bodyType member, just stringify it.
            return json.dumps(body)

    elif isinstance(body, str):
        print("stringify string before passing on")
        # just a string.  stringify it to make sure it's valid JSON and pass it on.
        return json.dumps(body)

    else:
        assert False


def incoming_message_to_test_script_object(message):
    """
    convert an object that we receive from IoTHub or EdgeHub into an object that
    our test scripts can understand
    """
    if isinstance(message.data, bytes):
        data = message.data.decode("utf-8")
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            pass
        return data
    else:
        return json.loads(message.data)
