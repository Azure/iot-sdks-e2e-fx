# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
from azure.iot.device.provisioning import ProvisioningDeviceClient


logger = logging.getLogger(__name__)


class InternalDeviceProvisioningGlueSync(object):
    def __init__(self):
        self.client = None

    def create_from_symmetric_key_sync(
        self, transport, provisioning_host, registration_id, id_scope, symmetric_key
    ):
        if transport == "mqtt":
            self.client = ProvisioningDeviceClient.create_from_symmetric_key(
                provisioning_host, registration_id, id_scope, symmetric_key
            )
        elif transport == "mqttws":
            self.client = ProvisioningDeviceClient.create_from_symmetric_key(
                provisioning_host,
                registration_id,
                id_scope,
                symmetric_key,
                websockets=True,
            )

    def create_from_x509_sync(
        self, transport, provisioning_host, registration_id, id_scope, x509
    ):
        assert False

    def register_sync(self):
        result = self.client.register()
        return {
            "status": result.status,
            "assigned_hub": result.registration_state.assigned_hub,
            "device_id": result.registration_state.device_id,
        }

    def destroy_sync(self):
        self.client = None
