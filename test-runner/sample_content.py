# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
import utilities

zero_size_payload = {}
minimum_payload = {"a": {}}


def make_message_payload(size=64):
    """
    make a random message payload with the given size
    """
    wrapper_overhead = len(json.dumps({"payload": ""}))
    if size == 0:
        return zero_size_payload
    elif size <= wrapper_overhead:
        return minimum_payload
    else:
        return {"payload": utilities.random_string(length=size - wrapper_overhead)}


def make_reported_props():
    return {"reported": {"foo": utilities.next_random_string("reported props")}}


def make_desired_props():
    return {"desired": {"foo": utilities.next_random_string("desired props")}}
