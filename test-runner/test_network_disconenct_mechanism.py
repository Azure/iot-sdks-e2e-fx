# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import msrest

pytestmark = pytest.mark.asyncio


@pytest.mark.describe("Network Disconnection Mechanism")
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.uses_v2_connect_group
class TestNetworkDisconnectMechanism(object):
    @pytest.mark.parametrize(
        "disconnection_type",
        [pytest.param("DROP", id="DROP"), pytest.param("REJECT", id="REJECT")],
    )
    @pytest.mark.it("Can disconnect and reconnect the network")
    async def test_disconnect_and_reconnect(
        self, disconnection_type, test_module_wrapper_api
    ):
        test_module_wrapper_api.network_disconnect(disconnection_type)
        test_module_wrapper_api.network_reconnect()

    @pytest.mark.it("Fails with an invalid disconnection type")
    async def test_invalid_disconnect_type(self, test_module_wrapper_api):
        with pytest.raises(Exception) as e_info:
            test_module_wrapper_api.network_disconnect("blah")
        assert e_info.value.__class__ in [
            ValueError,
            msrest.exceptions.HttpOperationError,
            msrest.exceptions.ClientRequestError,
        ]

    @pytest.mark.it("Does not fail if reconnecting without disconnecting")
    async def test_reconnect_only(self, test_module_wrapper_api):
        test_module_wrapper_api.network_reconnect()
