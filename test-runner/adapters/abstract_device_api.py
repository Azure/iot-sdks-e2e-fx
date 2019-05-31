# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractDeviceApi:
    @abc.abstractmethod
    def connect(self, transport, connection_string, ca_certificate):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def send_event(self, body):
        pass

    @abc.abstractmethod
    def enable_c2d(self):
        pass

    @abc.abstractmethod
    def wait_for_c2d_message_async(self):
        pass

    @abc.abstractmethod
    def enable_methods(self):
        pass

    @abc.abstractmethod
    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        pass

    @abc.abstractmethod
    def enable_twin(self):
        pass

    @abc.abstractmethod
    def get_twin(self):
        pass

    @abc.abstractmethod
    def patch_twin(self, patch):
        pass

    @abc.abstractmethod
    def wait_for_desired_property_patch_async(self):
        pass
