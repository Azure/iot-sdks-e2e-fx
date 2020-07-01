# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import json
from pathlib import Path

horton_settings_file_name = str(
    Path(__file__).parent.parent.joinpath("_horton_settings.json")
)

IOTHUB_CONNECTION_STRING_OLD_NAME = "IOTHUB_E2E_CONNECTION_STRING"
IOTEDGE_DEBUG_LOG_OLD_NAME = "IOTEDGE_DEBUG_LOG"


class HortonSettingsObject(object):
    pass


class HortonDeviceSettings(HortonSettingsObject):
    def __init__(self, name):
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


class HortonModuleSettings(HortonSettingsObject):
    def __init__(self, name):
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


class HortonSettings:
    def __init__(self):
        self.load()

    def _clear_settings(self):
        self.horton = HortonSettingsObject()
        self.horton.name = "horton"
        self.horton.image = None
        self.horton.language = None
        self.horton.transport = None

        self.iothub = HortonSettingsObject()
        self.iothub.name = "iothub"
        self.iothub.connection_string = None

        self.iotedge = HortonSettingsObject()
        self.iotedge.name = "iotedge"
        self.iotedge.device_id = None
        self.iotedge.connection_type = None
        self.iotedge.connection_string = None
        self.iotedge.ca_cert_base64 = None
        self.iotedge.debug_log = None
        self.iotedge.hostname = None

        self.test_module = HortonModuleSettings("test_module")
        self.friend_module = HortonModuleSettings("friend_module")
        self.leaf_device = HortonDeviceSettings("leaf_device")
        self.test_device = HortonDeviceSettings("test_device")
        self.perf_control_device = HortonDeviceSettings("perf_control_device")

        self.net_control = HortonSettingsObject()
        self.net_control.name = "net_control"
        self.net_control.host_port = 8140
        self.net_control.container_port = 8040
        self.net_control.adapter_address = "http://localhost:8140"
        self.net_control.test_destination = None
        self.net_control.api = None

        self._objects = [
            self.iothub,
            self.iotedge,
            self.test_module,
            self.friend_module,
            self.leaf_device,
            self.test_device,
            self.net_control,
            self.horton,
            self.perf_control_device,
        ]

    def load(self):
        self._clear_settings()

        # load settings from JSON
        try:
            with open(horton_settings_file_name) as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = {}

        # populate attributes from JSON settings
        for obj in self._objects:
            if obj.name in data:
                if type(data[obj.name]) == dict:
                    for key in data[obj.name]:
                        setattr(obj, key, data[obj.name][key])
                    del data[obj.name]
                else:
                    raise Exception("invalid value in json for key {}".format(key))

            # look for environment variables to override JSON settings
            for key in self._get_attribute_names(obj):
                env_name = "E2EFX_{}_{}".format(obj.name, key)
                if env_name in os.environ:
                    setattr(obj, key, os.environ[env_name])

        self._load_deprecated_environment_variables()

    def _load_deprecated_environment_variables(self):
        if IOTHUB_CONNECTION_STRING_OLD_NAME in os.environ:
            self.iothub.connection_string = os.environ[
                IOTHUB_CONNECTION_STRING_OLD_NAME
            ]

        if IOTEDGE_DEBUG_LOG_OLD_NAME in os.environ:
            self.iotedge.debug_log = os.environ[IOTEDGE_DEBUG_LOG_OLD_NAME]

    def _get_attribute_names(self, obj):
        return [
            i
            for i in dir(obj)
            if not i.startswith("_") and not callable(getattr(obj, i))
        ]

    def clear_object(self, obj):
        print("clearing {} object".format(obj.name))
        old_name = obj.name
        for attr in self._get_attribute_names(obj):
            setattr(obj, attr, None)
        obj.name = old_name

    def save(self):
        data = {}
        for obj in self._objects:
            for key in self._get_attribute_names(obj):
                if key != "name":
                    value = getattr(obj, key)
                    if value:
                        if obj.name not in data:
                            data[obj.name] = {}
                        data[obj.name][key] = value
        with open(horton_settings_file_name, "w") as outfile:
            json.dump(data, outfile, indent=2)


settings = HortonSettings()
