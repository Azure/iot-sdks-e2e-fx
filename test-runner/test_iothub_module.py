# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from base_client_tests import BaseClientTests
from telemetry_tests import TelemetryTests
from twin_tests import TwinTests


@pytest.mark.describe("IoTHubModuleClient")
@pytest.mark.testgroup_iothub_module_client
class TestIotHubModuleClient(BaseClientTests, TelemetryTests, TwinTests):
    @pytest.fixture
    def client(self, test_module):
        return test_module
