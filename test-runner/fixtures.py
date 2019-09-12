# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import pytest
import string
import random


def random_string(prefix=None):
    if prefix:
        s = prefix + ":"
    else:
        s = ""
    return s + "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(64)
    )


@pytest.fixture
def test_string():
    return random_string("String1")


@pytest.fixture
def test_string_2():
    return random_string("String2")


@pytest.fixture
def test_object_stringified(test_string):
    return '{ "message": "' + test_string + '" }'


@pytest.fixture
def test_object_stringified_2(test_string_2):
    return '{ "message": "' + test_string_2 + '" }'
