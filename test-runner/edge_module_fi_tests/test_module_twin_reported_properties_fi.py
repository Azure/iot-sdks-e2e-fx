# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
from runtime_config import get_current_config
from adapters import print_message
from edgehub_control import (
    edgeHub,
    disconnect_edgehub,
    connect_edgehub,
    restart_edgehub,
)
from time import sleep

pytestmark = pytest.mark.asyncio

@pytest.mark.timeout(180)
@pytest.mark.testgroup_edgehub_fault_injection
@pytest.mark.supportsTwin
async def test_module_can_set_reported_properties_and_service_can_retrieve_them_fi():
    try:
        reported_properties_sent = {"foo": random.randint(1, 9999)}
        print_message("connecting module client")
        module_client = connections.connect_test_module_client()
        print_message("enabling twin")
        await module_client.enable_twin()
        print_message("disabling edgehub")
        sleep(2)
        disconnect_edgehub()
        connect_edgehub()
        await module_client.patch_twin(reported_properties_sent)
        sleep(2)
        print_message("patched twin")
        print_message("disconnecting module client")
        module_client.disconnect_sync()
        print_message("module client disconnected")
        print_message("connecting registry client")
        registry_client = connections.connect_registry_client()
        print_message("disabling edgehub")
        sleep(2)
        disconnect_edgehub()
        connect_edgehub()
        sleep(2)
        print_message("reconnected edgehub")
        print_message("getting twin")
        twin_received = await registry_client.get_module_twin(
            get_current_config().test_module.device_id,
            get_current_config().test_module.module_id,
        )
        print_message("disconnecting registry client")
        registry_client.disconnect_sync()
        print_message("registry client disconnected")

        reported_properties_received = twin_received["properties"]["reported"]
        if "$version" in reported_properties_received:
            del reported_properties_received["$version"]
        if "$metadata" in reported_properties_received:
            del reported_properties_received["$metadata"]
        print_message("expected:" + str(reported_properties_sent))
        print_message("received:" + str(reported_properties_received))

        assert reported_properties_sent == reported_properties_received
    finally:
        restart_edgehub()
        sleep(5)
