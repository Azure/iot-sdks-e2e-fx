# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
from pathlib import Path
from dictionary_object import SimpleObject, DictionaryObject

horton_settings_file_name = str(
    Path(__file__).parent.parent.joinpath("_horton_settings.json")
)


all_environment_variables = {
    # old legacy variable names
    "IOTHUB_E2E_CONNECTION_STRING": "iothub.connection_string",
    "IOTEDGE_DEBUG_LOG": "iotedge.debug_log",
    # new variable names
    "HORTON_IOTHUB_CONNECTION_STRING": "iothub.connection_string",
    "HORTON_IOTEDGE_DEBUG_LOG": "iotedge.debug_log",
}


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
        self.adapter = ""
        self.host_port = ""
        self.container_port = ""
        self.container_name = ""
        self.capabilities = ""


class HortonDeviceSettings(ObjectWithAdapter):
    def __init__(self, name, object_type):
        super(HortonDeviceSettings, self).__init__(name, object_type)
        self.transport = ""
        self.connection_type = ""
        self.device_id = ""
        self.iothub_host_name = ""
        # for connection string connection
        self.connection_string = ""
        # for x5009 connection
        self.x509_cert_path = ""
        self.x509_key_path = ""
        # for symmetric key connection
        self.symmetric_key = ""


class HortonModuleSettings(ObjectWithAdapter):
    def __init__(self, name, object_type):
        super(HortonModuleSettings, self).__init__(name, object_type)
        self.transport = ""
        self.connection_type = ""
        self.device_id = ""
        self.module_id = ""
        self.iothub_host_name = ""
        # for connection string connection
        self.connection_string = ""
        # for x509 connection
        self.x509_cert_path = ""
        self.x509_key_path = ""


class Horton(SimpleObject):
    def __init__(self):
        super(Horton, self).__init__()
        self.name = "horton"
        self.image = ""
        self.language = ""
        self.transport = ""
        self.id_base = ""
        self.is_windows = ""
        self.machine_name = ""
        self.user_name = ""
        self.time_tag = ""


class IotHub(SimpleObject):
    def __init__(self):
        super(IotHub, self).__init__()
        self.name = "iothub"
        self.connection_string = ""
        self.iothub_host_name = ""


class IotEdge(SimpleObject):
    def __init__(self):
        super(IotEdge, self).__init__()
        self.name = "iotedge"
        self.device_id = ""
        self.connection_type = ""
        self.connection_string = ""
        self.ca_cert_base64 = ""
        self.debug_log = ""
        self.iotedge_host_name = ""


class SystemControl(ObjectWithAdapter):
    def __init__(self):
        super(SystemControl, self).__init__("system_control", "system_control")
        self.test_destination = ""


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
        self.system_control = SystemControl()

        self._objects = [
            self.iothub,
            self.iotedge,
            self.test_module,
            self.friend_module,
            self.leaf_device,
            self.test_device,
            self.system_control,
            self.horton,
        ]

    def load_environment_variables(self):
        """
        load environment variables into the HortonSettings object
        """

        for var_name in all_environment_variables:
            if var_name in os.environ:
                var_path = all_environment_variables[var_name]
                var_value = os.environ[var_name]

                # split the path into segments
                segments = var_path.split(".")
                segments.reverse()  # so we can use pop()

                # walk down the tree to find the node that holds the value
                obj = self
                while len(segments) > 1:
                    obj = getattr(obj, segments.pop())

                # set the value
                setattr(obj, segments.pop(), var_value)

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

settings.load_environment_variables()
