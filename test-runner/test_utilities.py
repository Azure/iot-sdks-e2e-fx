# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import ast


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
