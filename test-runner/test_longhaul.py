# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
from longhaul_config import DesiredTestProperties

pytestmark = pytest.mark.asyncio


desired_node_config = {
    "test_config": {
        "d2c": {"enabled": True, "interval": 1, "ops_per_interval": 5},
        "scenario": "test_longhaul_d2c_simple",
        "total_duration": "1:00:00",
    }
}


class LongHaulTest(object):
    async def test_longhaul(self, client):
        test_config = DesiredTestProperties.from_dict(desired_node_config).test_config


@pytest.mark.testgroup_iothub_device_2h_stress
@pytest.mark.describe("Device Client Long Run")
class TestDeviceClientLongHaul(LongHaulTest):
    @pytest.fixture
    def client(self, test_device):
        return test_device
