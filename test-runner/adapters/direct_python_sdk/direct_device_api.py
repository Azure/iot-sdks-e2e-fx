# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from multiprocessing.pool import ThreadPool
from internal_device_glue import InternalDeviceGlue
from ..abstract_device_api import AbstractDeviceApi

device_object_list = []


class DeviceApi(AbstractDeviceApi):
    def __init__(self):
        self.glue = InternalDeviceGlue()
        self.pool = ThreadPool()

    def connect(self, transport, connection_string, ca_certificate):
        device_object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        self.glue.connect(transport, connection_string, cert)

    def disconnect(self):
        if self in device_object_list:
            device_object_list.remove(self)

        self.glue.disconnect()
        self.glue = None

    def send_event(self, body):
        self.glue.send_event(body)

    def enable_c2d(self):
        self.glue.enable_c2d()

    def wait_for_c2d_message_async(self):
        return self.pool.apply_async(self.glue.wait_for_c2d_message)

    def enable_methods(self):
        self.glue.enable_methods()

    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        raise NotImplementedError
