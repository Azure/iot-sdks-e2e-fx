# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractDeviceProvisioningApi(object):
    @abc.abstractmethod
    def create_from_symmetric_key(
        self, transport, provisoing_host, registration_id, id_scope, symmetric_key
    ):
        pass

    @abc.abstractmethod
    def create_from_x509(
        self, transport, provisioning_host, registration_id, id_scope, x509
    ):
        pass

    @abc.abstractmethod
    def register(self):
        pass

    @abc.abstractmethod
    def destroy(self):
        pass
