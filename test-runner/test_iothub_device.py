# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from base_client_tests import BaseClientTests, ConnectionStatusTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests
from method_tests import (
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
)
from c2d_tests import C2dTests
from retry_tests import RetryTests


@pytest.mark.describe("IoTHub Device")
@pytest.mark.testgroup_iothub_device_client
class TestIotHubDeviceClient(
    BaseClientTests,
    TelemetryTests,
    TwinTests,
    ReceiveMethodCallFromServiceTests,
    C2dTests,
    ConnectionStatusTests,
    RetryTests,
):
    @pytest.fixture
    def client(self, test_device):
        return test_device
