# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import ast
import random
import string


def random_string(prefix=None, length=64):
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


_index = 0


def next_integer():
    global _index
    _index = _index + 1
    return _index


def next_random_string(prefix):
    return random_string("{} {}".format(prefix, next_integer()))
