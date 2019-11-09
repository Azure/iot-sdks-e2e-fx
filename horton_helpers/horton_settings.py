# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import json
import inspect
from pathlib import Path

horton_settings_file_name = str(
    Path(__file__).parent.parent.joinpath("_horton_settings.json")
)

IOTHUB_CONNECTION_STRING_OLD_NAME = "IOTHUB_E2E_CONNECTION_STRING"
IOTEDGE_DEBUG_LOG_OLD_NAME = "IOTEDGE_DEBUG_LOG"


class HortonSettingsObject(object):
    pass


class HortonSettings:
    def __init__(self):
        self.load()

    def _clear_settings(self):
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

        self.test_module = HortonSettingsObject()
        self.test_module.name = "test_module"
        self.test_module.module_id = "testMod"
        self.test_module.image = None
        self.test_module.device_id = None
        self.test_module.language = None
        self.test_module.adapter_address = None
        self.test_module.connection_type = None
        self.test_module.connection_string = None
        self.test_module.x509_cert_path = None
        self.test_module.x509_key_path = None
        self.test_module.host_port = None
        self.test_module.container_port = None

        self.friend_module = HortonSettingsObject()
        self.friend_module.name = "friend_module"
        self.friend_module.module_id = "friendMod"
        self.friend_module.image = None
        self.friend_module.device_id = None
        self.friend_module.language = None
        self.friend_module.adapter_address = None
        self.friend_module.connection_type = None
        self.friend_module.connection_string = None
        self.friend_module.x509_cert_path = None
        self.friend_module.x509_key_path = None
        self.friend_module.host_port = None
        self.friend_module.container_port = None

        self.leaf_device = HortonSettingsObject()
        self.leaf_device.name = "leaf_device"
        self.leaf_device.device_id = None
        self.leaf_device.language = None
        self.leaf_device.adapter_address = None
        self.leaf_device.connection_type = None
        self.leaf_device.connection_string = None
        self.leaf_device.x509_cert_path = None
        self.leaf_device.x509_key_path = None
        self.leaf_device.host_port = None
        self.leaf_device.container_port = None

        self.test_device = HortonSettingsObject()
        self.test_device.name = "test_device"
        self.test_device.device_id = None
        self.test_device.language = None
        self.test_device.adapter_address = None
        self.test_device.connection_type = None
        self.test_device.connection_string = None
        self.test_device.x509_cert_path = None
        self.test_device.x509_key_path = None
        self.test_device.host_port = None
        self.test_device.container_port = None

        self._objects = [
            self.iothub,
            self.iotedge,
            self.test_module,
            self.friend_module,
            self.leaf_device,
            self.test_device,
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
