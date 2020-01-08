# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from utilities import random_string
import pytest
import json

string_1K = random_string(prefix="1K-chars", length=1024)
string_64K = random_string(prefix="64K-chars", length=64 * 1024)
object_with_3_layers = {
    "layer_1_string": random_string("1"),
    "layer_2": {
        "layer_2_string": random_string("2"),
        "layer3": {"fake_number": 3, "fake_real_number": 1.87},
    },
}

telemetry_test_objects = [
    pytest.param(string_1K, id="1K character string"),
    pytest.param(string_64K, id="64k character string"),
    pytest.param(object_with_3_layers, id="object with 3 layers"),
]
