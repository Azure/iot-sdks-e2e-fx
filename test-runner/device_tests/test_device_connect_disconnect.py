#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections


@pytest.mark.testgroup_iothub_device_client
def test_device_client_connect_disconnect():
    device_client = connections.connect_test_device_client()
    device_client.disconnect()


@pytest.mark.testgroup_iothub_device_client
def test_device_client_connect_enable_methods_disconnect():
    device_client = connections.connect_test_device_client()
    device_client.enable_methods()
    device_client.disconnect()


@pytest.mark.testgroup_iothub_device_client
def test_device_client_connect_enable_input_messages_disconnect():
    device_client = connections.connect_test_device_client()
    device_client.enable_c2d()
    device_client.disconnect()
