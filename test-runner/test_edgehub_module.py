# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from base_client_tests import BaseClientTests, ConnectionStatusTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests
from input_output_tests import InputOutputTests
from method_tests import (
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
    InvokeMethodCallOnModuleTests,
    InvokeMethodCallOnLeafDeviceTests,
)
from retry_tests import RetryTests


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.describe("EdgeHub ModuleClient")
class TestIotHubModuleClient(
    BaseClientTests,
    TelemetryTests,
    TwinTests,
    InputOutputTests,
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
    InvokeMethodCallOnModuleTests,
    InvokeMethodCallOnLeafDeviceTests,
    ConnectionStatusTests,
    RetryTests,
):
    @pytest.fixture
    def client(self, test_module):
        return test_module
