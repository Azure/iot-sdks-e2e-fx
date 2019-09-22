# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from multiprocessing.pool import ThreadPool
from internal_device_glue import InternalDeviceGlue
from internal_module_glue import InternalModuleGlue
from ..abstract_iothub_apis import AbstractDeviceApi, AbstractModuleApi

device_object_list = []
module_object_list = []


class Connect(object):
    def connect_v1(self, transport, connection_string, ca_certificate):
        device_object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        self.glue.connect_v1(transport, connection_string, cert)

    def disconnect(self):
        if self in device_object_list:
            device_object_list.remove(self)

        if self in module_object_list:
            module_object_list.remove(self)

        self.glue.disconnect()
        self.glue = None


class ConnectFromEnvironment(object):
    def connect_from_environment_v1(self, transport):
        module_object_list.append(self)
        self.glue.connect_from_environment_v1(transport)


class Twin(object):
    def enable_twin(self):
        self.glue.enable_twin()

    def get_twin(self):
        return self.glue.get_twin()

    def patch_twin(self, patch):
        self.glue.send_twin_patch(patch)

    def wait_for_desired_property_patch_async(self):
        return self.pool.apply_async(self.glue.wait_for_desired_property_patch)


class Telemetry(object):
    def send_event(self, body):
        self.glue.send_event(body)

    def send_event_async(self, body):
        return self.pool.apply_async(self.glue.send_event, (body,))


class C2d(object):
    def enable_c2d(self):
        self.glue.enable_c2d()

    def wait_for_c2d_message_async(self):
        return self.pool.apply_async(self.glue.wait_for_c2d_message)


class InputsAndOutputs(object):
    def enable_input_messages(self):
        self.glue.enable_input_messages()

    def send_output_event(self, output_name, body):
        self.glue.send_output_event(output_name, body)

    def wait_for_input_event_async(self, input_name):
        return self.pool.apply_async(self.glue.wait_for_input_message, (input_name,))


class HandleMethods(object):
    def enable_methods(self):
        self.glue.enable_methods()

    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        class RequestAndResponse(object):
            pass

        request_and_response = RequestAndResponse()
        request_and_response.request_payload = request_payload
        request_and_response.response_payload = response_payload
        request_and_response.status_code = status_code
        return self.pool.apply_async(
            self.glue.roundtrip_method_call, (method_name, request_and_response)
        )


class InvokeMethods(object):
    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        return self.pool.apply_async(
            self.glue.invoke_module_method,
            (device_id, module_id, method_invoke_parameters),
        )

    def call_device_method_async(self, device_id, method_invoke_parameters):
        return self.pool.apply_async(
            self.glue.invoke_device_method, (device_id, method_invoke_parameters)
        )


class ConnectionStatus(object):
    def get_connection_status(self):
        return self.glue.get_connection_status()

    def wait_for_connection_status_change_async(self):
        return self.pool.apply_async(self.wait_for_connection_status_change)


class DeviceApi(
    Connect, Twin, Telemetry, C2d, HandleMethods, ConnectionStatus, AbstractDeviceApi
):
    def __init__(self):
        self.glue = InternalDeviceGlue()
        self.pool = ThreadPool()


class ModuleApi(
    Connect,
    ConnectFromEnvironment,
    Twin,
    Telemetry,
    InputsAndOutputs,
    HandleMethods,
    InvokeMethods,
    ConnectionStatus,
    AbstractModuleApi,
):
    def __init__(self):
        self.glue = InternalModuleGlue()
        self.pool = ThreadPool()
