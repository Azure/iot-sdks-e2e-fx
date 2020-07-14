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


class ObjectWithAdapter(SimpleObject):
    def __init__(self, name, object_type):
        super(ObjectWithAdapter, self).__init__()
        self.name = name
        self.object_type = object_type
        self.image = ""
        self.language = ""
        self.adapter_address = ""
        self.adapter = None
        self.host_port = ""
        self.container_port = ""
        self.container_name = ""
        self.capabilities = None


class HortonDeviceSettings(ObjectWithAdapter):
    def __init__(self, name, object_type):
        super(HortonDeviceSettings, self).__init__(name, object_type)
        self.device_id = ""
        self.connection_type = ""
        self.connection_string = ""
        self.x509_cert_path = ""
        self.x509_key_path = ""
        self.transport = "mqtt"
        self.registration_id = ""
        self.symmetric_key = ""
        self.hostname = ""


class HortonModuleSettings(ObjectWithAdapter):
    def __init__(self, name, object_type):
        super(HortonModuleSettings, self).__init__(name, object_type)
        self.device_id = ""
        self.module_id = ""
        self.connection_type = ""
        self.connection_string = ""
        self.x509_cert_path = ""
        self.x509_key_path = ""
        self.transport = "mqtt"


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


class System(ObjectWithAdapter):
    def __init__(self):
        super(System, self).__init__("system", "system")
        self.test_destination = ""


class DeviceProvisioning(ObjectWithAdapter):
    def __init__(self):
        super(DeviceProvisioning, self).__init__(
            "device_provisioning", "device_provisioning"
        )
        self.provisioning_host = ""
        self.id_scope = ""


class HortonSettings(DictionaryObject):
    def __init__(self):
        super(HortonSettings, self).__init__()

        self.horton = Horton()
        self.iothub = IotHub()
        self.iotedge = IotEdge()
        self.test_module = HortonModuleSettings("test_module", "iotedge_module")
        self.friend_module = HortonModuleSettings("friend_module", "iotedge_module")
        self.leaf_device = HortonDeviceSettings("leaf_device", "leaf_device")
        self.test_device = HortonDeviceSettings("test_device", "iotthub_device")
        self.longhaul_control_device = HortonDeviceSettings(
            "longhaul_control_device", "iothub_device"
        )
        self.device_provisioning = DeviceProvisioning()
        self.system = System()

        self._objects = [
            self.iothub,
            self.iotedge,
            self.test_module,
            self.friend_module,
            self.leaf_device,
            self.test_device,
            self.system,
            self.horton,
            self.longhaul_control_device,
            self.device_provisioning,
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
        for attr in obj._get_attribute_names():
            if attr not in ["name", "object_type"]:
                setattr(obj, attr, "")

    def save(self):
        self.to_file(horton_settings_file_name)


HortonSettings._defaults = HortonSettings()

try:
    settings = HortonSettings.from_file(horton_settings_file_name)
except FileNotFoundError:
    settings = HortonSettings()

settings.load_deprecated_environment_variables()
