#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
def test_module_client_connect_disconnect():
    module_client = connections.connect_test_module_client()
    module_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.supportsTwin
def test_module_client_connect_enable_twin_disconnect():
    module_client = connections.connect_test_module_client()
    module_client.enable_twin()
    module_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.receivesMethodCalls
def test_module_client_connect_enable_methods_disconnect():
    module_client = connections.connect_test_module_client()
    module_client.enable_methods()
    module_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.receivesInputMessages
def test_module_client_connect_enable_input_messages_disconnect():
    module_client = connections.connect_test_module_client()
    module_client.enable_input_messages()
    module_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
def test_registry_client_connect_disconnect():
    registry_client = connections.connect_registry_client()
    registry_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
def test_service_client_connect_disconnect():
    service_client = connections.connect_service_client()
    service_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.module_under_test_has_device_wrapper
def test_device_client_connect_disconnect():
    device_client = connections.connect_leaf_device_client()
    device_client.disconnect()


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.module_under_test_has_device_wrapper
def test_device_client_connect_enable_methods_disconnect():
    device_client = connections.connect_leaf_device_client()
    device_client.enable_methods()
    device_client.disconnect()
