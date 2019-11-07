# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import msrest
from timeouts import timeouts
from horton_settings import settings

pytestmark = pytest.mark.asyncio


@pytest.mark.describe("Network Disconnection Mechanism")
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.v2_connect_group
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
    async def test_disconnect_and_reconnect(
        self, disconnection_type, test_module_wrapper_api, test_module_transport
    ):
        await test_module_wrapper_api.network_disconnect(
            test_module_transport, disconnection_type
        )
        await test_module_wrapper_api.network_reconnect()

    @pytest.mark.it("Fails with an invalid transport")
    async def test_invalid_disconnect_type(
        self, test_module_wrapper_api, test_module_transport
    ):
        with pytest.raises(Exception) as e_info:
            await test_module_wrapper_api.network_disconnect("inalid_transport", "DROP")
        assert e_info.value.__class__ in [
            ValueError,
            msrest.exceptions.HttpOperationError,
            msrest.exceptions.ClientRequestError,
        ]

    @pytest.mark.it("Fails with an invalid disconnection type")
    async def test_invalid_transport(
        self, test_module_wrapper_api, test_module_transport
    ):
        with pytest.raises(Exception) as e_info:
            await test_module_wrapper_api.network_disconnect(
                test_module_transport, "invalid_disconnection_type"
            )
        assert e_info.value.__class__ in [
            ValueError,
            msrest.exceptions.HttpOperationError,
            msrest.exceptions.ClientRequestError,
        ]

    @pytest.mark.it("Does not fail if reconnecting without disconnecting")
    async def test_reconnect_only(self, test_module_wrapper_api):
        await test_module_wrapper_api.network_reconnect()

    @pytest.mark.it("Does not fail if reconnecting twice")
    async def test_reconnect_twice(
        self, test_module_wrapper_api, disconnection_type, test_module_transport
    ):
        await test_module_wrapper_api.network_disconnect(
            test_module_transport, disconnection_type
        )
        await test_module_wrapper_api.network_reconnect()
        await test_module_wrapper_api.network_reconnect()
