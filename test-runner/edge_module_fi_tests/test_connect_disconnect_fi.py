#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import sys
import pytest
import connections
from adapters import print_message as log_message
import urllib
from edgehub_control import (
    disconnect_edgehub,
    connect_edgehub,
    edgeHub,
    restart_edgehub,
)

"""
Test: test_module_client_connect_enable_twin_disconnect
Connect Module Client, enable twin on Module Client, bring down edgeHub, verify twin cannot connect, reconnect edgeHub, verify twin can connect.

Success:
Module Twin can reconnect to edgeHub after disconnection.

Failure: Upon edgeHub dropout, Module Twin cannot reconnect.
"""


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.supportsTwin
def test_module_client_connect_enable_twin_disconnect_fi():
    log_message("Connect Test Module Client")
    module_client = connections.connect_test_module_client()
    log_message("Enable Twin on Module Client")
    module_client.enable_twin()
    disconnect_edgehub()
    connect_edgehub()
    log_message("Disconnect Module Client")
    module_client.disconnect()


"""
Test: test_module_client_connect_enable_methods_disconnect

Success:
Module Twin can reconnect to edgeHub after disconnection.

Failure: Upon edgeHub dropout, Module Twin cannot reconnect.
"""


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.receivesMethodCalls
def test_module_client_connect_enable_methods_disconnect_fi():
    log_message("Connect Test Module Client")
    module_client = connections.connect_test_module_client()
    log_message("Enable Methods on Module Client")
    module_client.enable_methods()
    disconnect_edgehub()
    connect_edgehub()
    module_client.disconnect()


"""
Test:

Success: test_module_client_connect_enable_input_messages_disconnect
Module Twin can reconnect to edgeHub after disconnection.

Failure: Upon edgeHub dropout, Module Twin cannot reconnect.
"""


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.receivesInputMessages
def test_module_client_connect_enable_input_messages_disconnect_fi():
    module_client = connections.connect_test_module_client()
    log_message("Enable Input Messages on Module Client")
    module_client.enable_input_messages()
    disconnect_edgehub()  # Disconnecting Edgehub
    connect_edgehub()  # Reconnecting EdgeHub
    log_message("Disconnect Module Client")
    module_client.disconnect()


"""
Test:
Connect Module Client, enable twin on Module Client, bring down edgeHub, verify twin cannot connect, reconnect edgeHub, verify twin can connect.

Success:
Module Twin can reconnect to edgeHub after disconnection.

Failure: Upon edgeHub dropout, Module Twin cannot reconnect.
"""


@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.module_under_test_has_device_wrapper
def test_device_client_connect_enable_methods_disconnect_fi():
    device_client = connections.connect_leaf_device_client()
    device_client.enable_methods()
    device_client.disconnect()
