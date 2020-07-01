# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import json
from pathlib import Path
from dictionary_object import SimpleObject, DictionaryObject

horton_settings_file_name = str(
    Path(__file__).parent.parent.joinpath("_horton_settings.json")
)

IOTHUB_CONNECTION_STRING_OLD_NAME = "IOTHUB_E2E_CONNECTION_STRING"
IOTEDGE_DEBUG_LOG_OLD_NAME = "IOTEDGE_DEBUG_LOG"


class HortonDeviceSettings(SimpleObject):
    def __init__(self, name):
        super(HortonDeviceSettings, self).__init__()
        self.name = name
        self.device_id = None
        self.language = None
        self.adapter_address = None
        self.connection_type = None
        self.connection_string = None
        self.x509_cert_path = None
        self.x509_key_path = None
        self.host_port = None
        self.container_port = None
        self.container_name = None
        self.image = None
        self.object_type = None
        self.client = None


class HortonModuleSettings(SimpleObject):
    def __init__(self, name):
        super(HortonModuleSettings, self).__init__()
        self.name = name
        self.device_id = None
        self.module_id = None
        self.image = None
        self.language = None
        self.adapter_address = None
        self.connection_type = None
        self.connection_string = None
        self.x509_cert_path = None
        self.x509_key_path = None
        self.host_port = None
        self.container_port = None
        self.container_name = None
        self.image = None
        self.object_type = None
        self.client = None


class Horton(SimpleObject):
    def __init__(self):
        super(Horton, self).__init__()
        self.name = "horton"
        self.image = None
        self.language = None
        self.transport = None
        self.id_base = None


class IotHub(SimpleObject):
    def __init__(self):
        super(IotHub, self).__init__()
        self.name = "iothub"
        self.connection_string = None


class IotEdge(SimpleObject):
    def __init__(self):
        super(IotEdge, self).__init__()
        self.name = "iotedge"
        self.device_id = None
        self.connection_type = None
        self.connection_string = None
        self.ca_cert_base64 = None
        self.debug_log = None
        self.hostname = None


class NetControl(SimpleObject):
    def __init__(self):
        super(NetControl, self).__init__()
        self.name = "net_control"
        self.host_port = 8140
        self.container_port = 8040
        self.adapter_address = "http://localhost:8140"
        self.test_destination = None
        self.api = None

class HortonSettings(DictionaryObject):
    def __init__(self):
        super(HortonSettings, self).__init__()
        self.load()

    def _clear_settings(self):
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

    def load(self):
        self._clear_settings()

        # load settings from JSON
        try:
            with open(horton_settings_file_name) as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = {}

        if data:
            self.fill_from_dict(data)

        self._load_deprecated_environment_variables()

    def _load_deprecated_environment_variables(self):
        if IOTHUB_CONNECTION_STRING_OLD_NAME in os.environ:
            self.iothub.connection_string = os.environ[
                IOTHUB_CONNECTION_STRING_OLD_NAME
            ]

        if IOTEDGE_DEBUG_LOG_OLD_NAME in os.environ:
            self.iotedge.debug_log = os.environ[IOTEDGE_DEBUG_LOG_OLD_NAME]

    def clear_object(self, obj):
        print("clearing {} object".format(obj.name))
        old_name = obj.name
        for attr in self._get_attribute_names(obj):
            setattr(obj, attr, None)
        obj.name = old_name

    def save(self):
        self.to_file(horton_settings_file_name)


settings = HortonSettings()
