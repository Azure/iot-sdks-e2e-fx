#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import string
import random
import json
import ast

maximum_message_length = 64  # * 1024


def random_string(length):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
    )


def random_string_in_json():
    return '{ "message": "' + max_random_string() + '" }'


def max_random_string():
    return random_string(maximum_message_length)


def json_is_same(a, b):
    # If either parameter is a string, convert it to an object.
    # use ast.literal_eval because they might be single-quote delimited which fails with json.loads.
    if isinstance(a, str):
        a = ast.literal_eval(a)
    if isinstance(b, str):
        b = ast.literal_eval(b)
    return a == b


def assert_json_equality(a, b):
    assert json_is_same(a, b)


default_eventhub_timeout = 30
