# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import msrest


@pytest.mark.describe("Network Disconnection Mechanism")
@pytest.mark.testgroup_iothub_device_client
@pytest.mark.testgroup_iothub_module_client
@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.uses_network_disconnect
class TestNetworkDisconnectMechanism(object):
    @pytest.mark.parametrize(
        "disconnect_type",
        [pytest.param("DROP", id="DROP"), pytest.param("REJECT", id="REJECT")],
    )
    @pytest.mark.it("Can disconnect and reconnect the network")
    def test_disconnect_and_reconnect(self, disconnect_type, test_module_wrapper_api):
        test_module_wrapper_api.network_disconnect(disconnect_type)
        test_module_wrapper_api.network_reconnect()

    @pytest.mark.it("Fails with an invalid disconnection type")
    def test_invalid_disconnect_type(self, test_module_wrapper_api):
        with pytest.raises(Exception) as e_info:
            test_module_wrapper_api.network_disconnect("blah")
        assert isinstance(e_info.value, ValueError) or isinstance(
            e_info.value, msrest.exceptions.HttpOperationError
        )

    @pytest.mark.it("Does not fail if reconnecting without disconnecting")
    def test_reconnect_only(self, test_module_wrapper_api):
        test_module_wrapper_api.network_reconnect()
