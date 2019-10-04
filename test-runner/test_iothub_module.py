# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import dropped_connection_tests
from base_client_tests import BaseClientTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests

pytestmark = pytest.mark.asyncio


class IoTHubModuleClient(object):
    @pytest.fixture
    def client(self, test_module):
        return test_module


@pytest.mark.describe("IoTHubModuleClient")
@pytest.mark.testgroup_iothub_module_client
class TestIotHubModuleClient(
    IoTHubModuleClient, BaseClientTests, TelemetryTests, TwinTests
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - dropping but not disconnected"
)
@pytest.mark.testgroup_iothub_module_client
class TestIoTHubModuleDroppingButNotDisconnected(
    IoTHubModuleClient,
    dropped_connection_tests.CallMethodBeforeOnDisconnected,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass
