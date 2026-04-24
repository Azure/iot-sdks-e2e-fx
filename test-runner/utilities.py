# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import ast
import asyncio
import random
import string

from horton_logging import logger


async def connect2_with_retry(client, retries=3, delay=5):
    """Retry connect2() on transient failures (e.g. MQTT CONNACK not received
    within paho's keepalive window).  Only use in positive tests that expect
    connect to succeed; negative/regression tests should call connect2() directly
    so they see the real exception immediately."""
    last_exc = None
    for attempt in range(retries):
        try:
            await client.connect2()
            return
        except Exception as e:
            last_exc = e
            logger(
                "connect2 attempt {} failed ({}); retrying in {}s".format(
                    attempt + 1, e, delay
                )
            )
            await asyncio.sleep(delay)
    raise last_exc

default_length = 64


def random_string(prefix=None, length=default_length):
    if prefix:
        s = prefix + ":"
    else:
        s = ""
    return (
        s
        + "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
        )[:length]
    )


def json_is_same(a, b):
    if a == b:
        return True
    else:
        # If either parameter is a string, convert it to an object.
        # use ast.literal_eval because they might be single-quote delimited which fails with json.loads.
        if isinstance(a, str):
            a = ast.literal_eval(a)
        if isinstance(b, str):
            b = ast.literal_eval(b)
        return a == b


def assert_json_equality(a, b):
    assert json_is_same(a, b)


_index = {}


def next_integer(prefix):
    """
    return the next integer in the sequence using the given prefix as an index
    """
    global _index
    if prefix in _index:
        _index[prefix] += 1
    else:
        _index[prefix] = 1
    return _index[prefix]


def next_random_string(prefix, length=default_length):
    """
    return a random string with the given prefix
    """
    return random_string("{} {}".format(prefix, next_integer(prefix)), length=length)
