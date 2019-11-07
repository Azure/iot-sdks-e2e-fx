# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from timeouts import timeouts
from base_client_tests import BaseClientTests
from method_tests import (
    ReceiveMethodCallFromServiceTests,
    ReceiveMethodCallFromModuleTests,
)

pytestmark = pytest.mark.asyncio


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.describe("Edge Leaf Device")
@pytest.mark.timeout(timeouts.generic_test_timeout)
class TestEdgeHubLeafDevice(
    BaseClientTests, ReceiveMethodCallFromServiceTests, ReceiveMethodCallFromModuleTests
):
    @pytest.fixture
    def client(self, leaf_device):
        return leaf_device
