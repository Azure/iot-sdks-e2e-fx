# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from base_client_tests import BaseClientTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests
from input_output_tests import InputOutputTests
from method_tests import (
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
    InvokeMethodCallOnModuleTests,
    InvokeMethodCallOnLeafDeviceTests,
)
import dropped_connection_tests

pytestmark = pytest.mark.asyncio


class EdgeHubModuleClient(object):
    @pytest.fixture
    def client(self, test_module):
        return test_module


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.describe("EdgeHub ModuleClient")
class TestEdgeHubModuleClient(
    EdgeHubModuleClient,
    BaseClientTests,
    TelemetryTests,
    TwinTests,
    InputOutputTests,
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
    InvokeMethodCallOnModuleTests,
    InvokeMethodCallOnLeafDeviceTests,
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "EdgeHub Module Client dropped connections - dropping but not disconnected"
)
@pytest.mark.testgroup_edgehub_module_client
class TestEdgeHubModuleDroppingButNotDisconnected(
    EdgeHubModuleClient,
    dropped_connection_tests.CallMethodBeforeOnDisconnected,
    dropped_connection_tests.DroppedConnectionEdgeHubModuleTests,
):
    pass
