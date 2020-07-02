# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from timeouts import timeouts
import dropped_connection_tests
import drop_scenario
from base_client_tests import BaseClientTests
from method_tests import ReceiveMethodCallFromServiceTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests
from regression_tests import RegressionTests

pytestmark = pytest.mark.asyncio


class IoTHubModuleClient(object):
    @pytest.fixture
    def client(self, test_module):
        return test_module


@pytest.mark.describe("IoTHubModuleClient")
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.timeout(timeouts.generic_test_timeout)
class TestIotHubModuleClient(
    IoTHubModuleClient,
    BaseClientTests,
    TelemetryTests,
    TwinTests,
    ReceiveMethodCallFromServiceTests,
    RegressionTests,
):
    pass


@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - network glitched and client still connected"
)
@pytest.mark.testgroup_iothub_module_quick_drop
@pytest.mark.testgroup_iothub_module_full_drop
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubModuleNetworkGlitchClientConnected(
    IoTHubModuleClient,
    drop_scenario.NetworkGlitchClientConnected,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass


@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - network glitched and client disconencted"
)
@pytest.mark.testgroup_iothub_module_full_drop
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubModuleNetworkGlitchClientDisconnected(
    IoTHubModuleClient,
    drop_scenario.NetworkGlitchClientDisconnected,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass
