# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from timeouts import timeouts
from base_client_tests import BaseClientTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests
from method_tests import (
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
)
from c2d_tests import C2dTests
import dropped_connection_tests

pytestmark = pytest.mark.asyncio


class IoTHubDeviceClient(object):
    @pytest.fixture
    def client(self, test_device):
        return test_device


@pytest.mark.describe("IoTHub Device")
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.timeout(timeouts.generic_test_timeout)
class TestIotHubDeviceClient(
    IoTHubDeviceClient,
    BaseClientTests,
    TelemetryTests,
    TwinTests,
    ReceiveMethodCallFromServiceTests,
    C2dTests,
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "IoTHub DeviceClient dropped connections - dropping but not disconnected"
)
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubDeviceDroppingButNotDisconnected(
    IoTHubDeviceClient,
    dropped_connection_tests.CallMethodBeforeOnDisconnected,
    dropped_connection_tests.DroppedConnectionIoTHubDeviceTests,
):
    pass
