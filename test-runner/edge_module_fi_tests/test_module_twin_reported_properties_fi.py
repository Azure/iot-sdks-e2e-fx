# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import random
import connections
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
async def test_module_can_set_reported_properties_and_service_can_retrieve_them_fi(
    logger
):
    try:
        reported_properties_sent = {"foo": random.randint(1, 9999)}
        logger("connecting module client")
        module_client = connections.connect_test_module_client()
        logger("enabling twin")
        await module_client.enable_twin()
        logger("disabling edgehub")
        sleep(2)
        disconnect_edgehub()
        connect_edgehub()
        await module_client.patch_twin(reported_properties_sent)
        sleep(2)
        logger("patched twin")
        logger("disconnecting module client")
        module_client.disconnect_sync()
        logger("module client disconnected")
        logger("connecting registry client")
        registry_client = connections.connect_registry_client()
        logger("disabling edgehub")
        sleep(2)
        disconnect_edgehub()
        connect_edgehub()
        sleep(2)
        logger("reconnected edgehub")
        logger("getting twin")
        twin_received = await registry_client.get_module_twin(
            module_client.device_id, module_client.module_id
        )
        logger("disconnecting registry client")
        registry_client.disconnect_sync()
        logger("registry client disconnected")

        reported_properties_received = twin_received["properties"]["reported"]
        if "$version" in reported_properties_received:
            del reported_properties_received["$version"]
        if "$metadata" in reported_properties_received:
            del reported_properties_received["$metadata"]
        logger("expected:" + str(reported_properties_sent))
        logger("received:" + str(reported_properties_received))

        assert reported_properties_sent == reported_properties_received
    finally:
        restart_edgehub()
        sleep(5)
