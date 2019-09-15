# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from utilities import random_string
import pytest
import json

string_64 = random_string("64-chars", length=64)
string_1K = random_string(prefix="1K-chars", length=1024)
string_2000 = random_string(prefix="2000-chars", length=2000)
string_64K = random_string(prefix="64K-chars", length=64 * 1024)

simple_object = {"64_chars": random_string(length=64)}
simple_object_stringified = json.dumps(simple_object)

object_with_3_layers = {
    "layer_1_string": random_string("1"),
    "layer_2": {
        "layer_2_string": random_string("2"),
        "layer3": {"fake_number": 3, "fake_real_number": 1.87},
    },
}
object_with_3_layers_stringified = json.dumps(object_with_3_layers)

telemetry_test_objects = [
    pytest.param(string_64, id="64 character string"),
    pytest.param(string_1K, id="1K character string"),
    pytest.param(string_2000, id="2000 character string"),
    pytest.param(string_64K, id="64k character string"),
    pytest.param(simple_object, id="simple object"),
    pytest.param(simple_object_stringified, id="simple object, as string"),
    pytest.param(object_with_3_layers, id="object with 3 layers"),
    pytest.param(
        object_with_3_layers_stringified, id="object with 3 layers, as string"
    ),
]
