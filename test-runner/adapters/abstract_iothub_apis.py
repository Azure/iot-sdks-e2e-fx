# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class ServiceConnectDisconnect(object):
    @abc.abstractmethod
    def connect_sync(self, connection_string):
        pass

    @abc.abstractmethod
    def disconnect_sync(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class Connect(object):
    @abc.abstractmethod
    def connect_sync(self, transport, connection_string, ca_certificate):
        pass

    @abc.abstractmethod
    def disconnect_sync(self):
        pass

    @abc.abstractmethod
    def create_from_connection_string_sync(
        self, transport, connection_string, ca_certificate
    ):
        pass

    @abc.abstractmethod
    def create_from_x509_sync(self, transport, x509):
        pass

    @abc.abstractmethod
    def connect2(self):
        pass

    @abc.abstractmethod
    def reconnect(self, force_password_renewal=False):
        pass

    @abc.abstractmethod
    def disconnect2(self):
        pass

    @abc.abstractmethod
    def destroy_sync(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class ConnectFromEnvironment(object):
    @abc.abstractmethod
    def connect_from_environment_sync(self, transport):
        pass

    @abc.abstractmethod
    def create_from_environment_sync(self, transport):
        pass


@six.add_metaclass(abc.ABCMeta)
class Twin(object):
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
    def wait_for_desired_property_patch(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class HandleMethods(object):
    @abc.abstractmethod
    def enable_methods(self):
        pass

    @abc.abstractmethod
    def roundtrip_method_call(
        self, method_name, status_code, request_payload, response_payload
    ):
        pass


@six.add_metaclass(abc.ABCMeta)
class Telemetry(object):
    @abc.abstractmethod
    def send_event(self, body):
        pass


@six.add_metaclass(abc.ABCMeta)
class InputsAndOutputs(object):
    @abc.abstractmethod
    def enable_input_messages(self):
        pass

    @abc.abstractmethod
    def send_output_event(self, output_name, body):
        pass

    @abc.abstractmethod
    def wait_for_input_event(self, input_name):
        pass


@six.add_metaclass(abc.ABCMeta)
class InvokeMethods(object):
    @abc.abstractmethod
    def call_module_method(self, device_id, module_id, method_invoke_parameters):
        pass

    @abc.abstractmethod
    def call_device_method(self, device_id, method_invoke_parameters):
        pass


@six.add_metaclass(abc.ABCMeta)
class ConnectionStatus(object):
    @abc.abstractmethod
    def get_connection_status(self):
        pass

    @abc.abstractmethod
    def wait_for_connection_status_change(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class C2d(object):
    @abc.abstractmethod
    def enable_c2d(self):
        pass

    @abc.abstractmethod
    def wait_for_c2d_message(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class ServiceSideOfTwin(object):
    @abc.abstractmethod
    def get_module_twin(self, device_id, module_id):
        pass

    @abc.abstractmethod
    def patch_module_twin(self, device_id, module_id, patch):
        pass

    @abc.abstractmethod
    def get_device_twin(self, device_id):
        pass

    @abc.abstractmethod
    def patch_device_twin(self, device_id, patch):
        pass


@six.add_metaclass(abc.ABCMeta)
class AbstractModuleApi(
    Connect,
    ConnectFromEnvironment,
    Telemetry,
    Twin,
    InputsAndOutputs,
    HandleMethods,
    InvokeMethods,
    ConnectionStatus,
):
    pass


@six.add_metaclass(abc.ABCMeta)
class AbstractDeviceApi(Connect, C2d, Telemetry, Twin, HandleMethods, ConnectionStatus):
    pass


@six.add_metaclass(abc.ABCMeta)
class AbstractRegistryApi(ServiceConnectDisconnect, ServiceSideOfTwin):
    pass


@six.add_metaclass(abc.ABCMeta)
class AbstractServiceApi(ServiceConnectDisconnect, InvokeMethods):

    @abc.abstractmethod
    def send_c2d(self, device_id, message):
        pass


