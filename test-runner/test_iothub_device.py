# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from base_client_tests import BaseClientTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests
from method_tests import (
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
)
from c2d_tests import C2dTests


@pytest.mark.describe("IoTHub Device")
@pytest.mark.testgroup_iothub_device_client
class TestIotHubModuleClient(
    BaseClientTests,
    TelemetryTests,
    TwinTests,
    ReceiveMethodCallFromServiceTests,
    C2dTests,
):
    @pytest.fixture
    def client(self, test_device):
        return test_device
