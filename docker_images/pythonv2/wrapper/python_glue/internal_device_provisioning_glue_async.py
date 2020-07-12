# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging

logger = logging.getLogger(__name__)


class InternalDeviceProvisioningGlueAsync(object):
    def __init__(self):
        self.client = None

    async def create_from_symmetric_key(
        self, transport, provisoing_host, registration_id, id_scope, symmetric_key
    ):
        # BKTODO
        pass

    async def create_from_x509(
        self, transport, provisioning_host, registration_id, id_scope, x509
    ):
        # BKTODO
        pass

    async def register(self):
        # BKTODO
        pass

    async def destroy(self):
        # BKTODO
        pass
