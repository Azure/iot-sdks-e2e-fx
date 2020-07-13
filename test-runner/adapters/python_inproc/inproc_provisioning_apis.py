# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from internal_glue_factory import create_glue_object
from ..abstract_provisioning_apis import AbstractDeviceProvisioningApi

provisioning_object_list = []


class PythonDirectRegistrationResult(object):
    def __init__(self):
        self.status = None
        self.device_id = None
        self.assigned_hub = None


class DeviceProvisioningApi(AbstractDeviceProvisioningApi):
    def __init__(self):
        self.glue = create_glue_object("device_provisioning", "async_interface")

    async def create_from_symmetric_key(
        self, transport, provisioning_host, registration_id, id_scope, symmetric_key
    ):
        provisioning_object_list.append(self)
        await self.glue.create_from_symmetric_key(
            transport, provisioning_host, registration_id, id_scope, symmetric_key
        )

    async def create_from_x509(
        self, transport, provisioning_host, registration_id, id_scope, x509
    ):
        provisioning_object_list.append(self)
        await self.glue.create_from_x509(
            transport, provisioning_host, registration_id, id_scope, x509
        )

    async def register(self):
        result = await self.glue.register()
        obj = PythonDirectRegistrationResult()
        obj.status = result["status"]
        obj.device_id = result["device_id"]
        obj.assigned_hub = result["assigned_hub"]
        return obj

    async def destroy(self):
        if self in provisioning_object_list:
            provisioning_object_list.remove(self)
        await self.glue.destroy()
