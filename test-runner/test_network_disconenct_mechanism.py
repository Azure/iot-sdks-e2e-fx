# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import msrest
from timeouts import timeouts
from horton_settings import settings
import limitations

pytestmark = pytest.mark.asyncio


@pytest.mark.skip(reason="")
@pytest.mark.describe("Network Disconnection Mechanism")
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.timeout(timeouts.generic_test_timeout)
class TestNetworkDisconnectMechanism(object):
    @pytest.fixture(
        params=[
            pytest.param("DROP", id="use iptables DROP"),
            pytest.param("REJECT", id="use iptables REJECT"),
        ]
    )
    def disconnection_type(self, request):
        return request.param

    @pytest.fixture
    def test_module_transport(self):
        return settings.test_module.transport

    @pytest.mark.it("Can disconnect and reconnect the network")
    async def test_disconnect_and_reconnect(self, disconnection_type, system_control):
        limitations.skip_if_no_system_control()
        await system_control.disconnect_network(disconnection_type)
        await system_control.reconnect_network()

    @pytest.mark.it("Fails with an invalid disconnection type")
    async def test_invalid_transport(self, system_control):
        limitations.skip_if_no_system_control()
        with pytest.raises(Exception) as e_info:
            await system_control.disconnect_network("invalid_disconnection_type")
        assert e_info.value.__class__ in [
            ValueError,
            msrest.exceptions.HttpOperationError,
            msrest.exceptions.ClientRequestError,
        ]

    @pytest.mark.it("Does not fail if reconnecting without disconnecting")
    async def test_reconnect_only(self, system_control):
        limitations.skip_if_no_system_control()
        await system_control.reconnect_network()

    @pytest.mark.it("Does not fail if reconnecting twice")
    async def test_reconnect_twice(self, system_control, disconnection_type):
        limitations.skip_if_no_system_control()
        await system_control.disconnect_network(disconnection_type)
        await system_control.reconnect_network()
        await system_control.reconnect_network()
