# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from timeouts import timeouts
import dropped_connection_tests
import drop_situation
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
@pytest.mark.timeout(timeouts.generic_test_timeout)
class TestIotHubModuleClient(
    IoTHubModuleClient, BaseClientTests, TelemetryTests, TwinTests
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - network dropped and client still connected"
)
@pytest.mark.testgroup_iothub_module_drop
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubModuleNetworkDroppedAndClientStillConnected(
    IoTHubModuleClient,
    drop_situation.NetworkDroppedAndClientStillConnected,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - network dropped and client disconencted"
)
@pytest.mark.testgroup_iothub_module_drop
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubModuleNetworkDroppedAndClientDisconnected(
    IoTHubModuleClient,
    drop_situation.NetworkDroppedAndClientDisconnected,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - client disconencted with network available"
)
@pytest.mark.testgroup_iothub_module_drop
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubModuleClientDisconnectedAndNetworkAvailable(
    IoTHubModuleClient,
    drop_situation.ClientDisconnectedAndNetworkAvailable,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass


@pytest.mark.dropped_connection_tests
@pytest.mark.describe(
    "IoTHub ModuleClient dropped connections - client disconencted with network not available"
)
@pytest.mark.testgroup_iothub_module_drop
@pytest.mark.timeout(timeouts.dropped_connection_test_timeout)
class TestIoTHubModuleClientDisconnectedAndNetworkNotAvailable(
    IoTHubModuleClient,
    drop_situation.ClientDisconnectedAndNetworkNotAvailable,
    dropped_connection_tests.DroppedConnectionIoTHubModuleTests,
):
    pass
