# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
from pathlib import Path
from dictionary_object import SimpleObject, DictionaryObject

horton_settings_file_name = str(
    Path(__file__).parent.parent.joinpath("_horton_settings.json")
)

IOTHUB_CONNECTION_STRING_OLD_NAME = "IOTHUB_E2E_CONNECTION_STRING"
IOTEDGE_DEBUG_LOG_OLD_NAME = "IOTEDGE_DEBUG_LOG"

# set defaults to "" or 0.  If we use "None", then the serialization in dictionary_object.py
# saves all the None values to json and we don't want that.


class HortonDeviceSettings(SimpleObject):
    def __init__(self, name):
        super(HortonDeviceSettings, self).__init__()
        self.name = name
        self.device_id = ""
        self.language = ""
        self.adapter_address = ""
        self.connection_type = ""
        self.connection_string = ""
        self.x509_cert_path = ""
        self.x509_key_path = ""
        self.host_port = ""
        self.container_port = ""
        self.container_name = ""
        self.image = ""
        self.object_type = ""
        self.client = ""


class HortonModuleSettings(SimpleObject):
    def __init__(self, name):
        super(HortonModuleSettings, self).__init__()
        self.name = name
        self.device_id = ""
        self.module_id = ""
        self.image = ""
        self.language = ""
        self.adapter_address = ""
        self.connection_type = ""
        self.connection_string = ""
        self.x509_cert_path = ""
        self.x509_key_path = ""
        self.host_port = ""
        self.container_port = ""
        self.container_name = ""
        self.image = ""
        self.object_type = ""
        self.client = ""


class Horton(SimpleObject):
    def __init__(self):
        super(Horton, self).__init__()
        self.name = "horton"
        self.image = ""
        self.language = ""
        self.transport = ""
        self.id_base = ""
        self.is_windows = ""


class IotHub(SimpleObject):
    def __init__(self):
        super(IotHub, self).__init__()
        self.name = "iothub"
        self.connection_string = ""


class IotEdge(SimpleObject):
    def __init__(self):
        super(IotEdge, self).__init__()
        self.name = "iotedge"
        self.device_id = ""
        self.connection_type = ""
        self.connection_string = ""
        self.ca_cert_base64 = ""
        self.debug_log = ""
        self.hostname = ""


class NetControl(SimpleObject):
    def __init__(self):
        super(NetControl, self).__init__()
        self.name = "net_control"
        self.host_port = ""
        self.container_port = ""
        self.adapter_address = ""
        self.test_destination = ""
        self.api = ""


class HortonSettings(DictionaryObject):
    def __init__(self):
        super(HortonSettings, self).__init__()

        self.horton = Horton()
        self.iothub = IotHub()
        self.iotedge = IotEdge()
        self.test_module = HortonModuleSettings("test_module")
        self.friend_module = HortonModuleSettings("friend_module")
        self.leaf_device = HortonDeviceSettings("leaf_device")
        self.test_device = HortonDeviceSettings("test_device")
        self.net_control = NetControl()

        self._objects = [
            self.iothub,
            self.iotedge,
            self.test_module,
            self.friend_module,
            self.leaf_device,
            self.test_device,
            self.net_control,
            self.horton,
        ]

    def load_deprecated_environment_variables(self):
        if IOTHUB_CONNECTION_STRING_OLD_NAME in os.environ:
            self.iothub.connection_string = os.environ[
                IOTHUB_CONNECTION_STRING_OLD_NAME
            ]

        if IOTEDGE_DEBUG_LOG_OLD_NAME in os.environ:
            self.iotedge.debug_log = os.environ[IOTEDGE_DEBUG_LOG_OLD_NAME]

    def clear_object(self, obj):
        print("clearing {} object".format(obj.name))
        old_name = obj.name
        for attr in obj._get_attribute_names():
            setattr(obj, attr, "")
        obj.name = old_name

    def save(self):
        self.to_file(horton_settings_file_name)


HortonSettings._defaults = HortonSettings()

try:
    settings = HortonSettings.from_file(horton_settings_file_name)
except FileNotFoundError:
    settings = HortonSettings()

settings.load_deprecated_environment_variables()
