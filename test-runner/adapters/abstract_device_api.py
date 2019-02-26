# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractDeviceApi:

    @abc.abstractmethod
    async def connect(self, transport, connection_string, ca_certificate):
        pass

    @abc.abstractmethod
    async def disconnect(self):
        pass

    @abc.abstractmethod
    async def send_event(self, body):
        pass

    @abc.abstractmethod
    async def receive_c2d(self):
        pass

    @abc.abstractmethod
    async def enable_methods(self):
        pass

    @abc.abstractmethod
    async def roundtrip_method_async(self, method_name, status_code, request_payload, response_payload):
        pass
