#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_create_identities.py
# author:   v-greach@microsoft.com 

import sys
import os
import json
import pathlib
import traceback
from colorama import init, Fore, Back, Style
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '../horton_helpers')))
from service_helper import Helper

class HortonCreateIdentities:

    def __init__(self, input_manifest_file, save_manifest_file=''):
        init(convert=True)
        self.horton_create_identities( input_manifest_file, save_manifest_file)

    def horton_create_identities(self, input_manifest_file, save_manifest_file=''):
        hub_connect_string = self.get_env_connect_string()
        if not save_manifest_file:
            save_manifest_file = input_manifest_file
        deployment_json = self.get_deployment_model_json(input_manifest_file)
        az_devices = []
        module_count = 0

        try:
            deployment_name = deployment_json["deploymentName"]
            deployment_containers = deployment_json['containers']
            identity_json = deployment_json['identities']
            id_prefix = "horton_{}_{}".format(self.get_random_num_string(1000),self.get_random_num_string(1000))
            deployment_name += '_' + id_prefix
            for azure_device in identity_json:
                az_device_id = identity_json[azure_device]
                objectType = self.get_json_value(az_device_id, 'objectType')
                objectName = self.get_json_value(az_device_id, 'objectName')
                if objectType == "iothub_device":
                    device_id = "{}_{}".format(id_prefix, objectName)
                    dev_object = self.populate_device_object(az_device_id, objectName, device_id)
                    dev_object.connectionString = self.create_iot_device(hub_connect_string, device_id)
                    dev_object.deviceId = device_id
                    child_modules = []
                    if(self.node_has_children(identity_json, azure_device, 'modules')):
                        modules = identity_json[azure_device]['modules']
                        for module in modules:
                            module_obj = self.populate_device_object(modules[module], module, device_id)
                            module_obj.deviceId = device_id
                            module_obj.moduleId = module
                            module_obj.connectionString = self.create_device_module(hub_connect_string, device_id, module)
                            child_modules.append(module_obj)
                            module_count += 1

                    if(len(child_modules) > 0):
                        dev_object.modules = child_modules
                    az_devices.append(dev_object)

                elif(objectType in ["iothub_service", "iothub_registry"]):
                    dev_object = self.populate_device_object(az_device_id, objectName, 'None')
                    dev_object.connectionString = hub_connect_string
                    az_devices.append(dev_object)

        except Exception as e:
            print(Fore.RED + "Exception Processing HortonManifest: " + input_manifest_file, file=sys.stderr)
            print(str(e) + Fore.RESET, file=sys.stderr)
            return

        print(Fore.GREEN + "Created {} Devices and {} Modules".format(len(az_devices), module_count) + Fore.RESET)

        # add device id's and connection strings back to horton_manifest & save it
        deployment_obj = DeploymentObject(deployment_name, az_devices, deployment_containers)
        new_manifest_json = json.dumps(deployment_obj, default = lambda x: x.__dict__, sort_keys=False, indent=2)
        try:
            with open(save_manifest_file, 'w') as f:
                f.write(new_manifest_json)
        except:
            print(Fore.RED + "ERROR: writing JSON manifest to: " + save_manifest_file + Fore.RESET, file=sys.stderr)

        print("create_hotron_devices_from_manifest Complete")
        return True

    def populate_device_object(self, device_json, object_name, deviceId=''):
        device_object = DeviceObject(object_name)
        if deviceId:
            if deviceId != 'None':
                device_object.deviceId     = deviceId
        else:
            device_object.deviceId      = self.get_json_value(device_json, 'deviceId')
        device_object.objectName        = self.get_json_value(device_json, 'objectName')
        device_object.objectType        = self.get_json_value(device_json, 'objectType')
        device_object.apiSurface        = self.get_json_value(device_json, 'apiSurface')
        device_object.adapterName       = self.get_json_value(device_json, 'adapterName')
        device_object.tcpPort           = self.get_json_value(device_json, 'tcpPort')
        device_object.connectionString  = self.get_json_value(device_json, 'connectionString')
        return device_object

    def node_has_children(self, json, node, name):
        try:
            children = json[node]
            if(children):
                if(children[name]):
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False

    def get_json_value(self, node, name):
        value = ""
        try:
            value = node[name]
        except:
            print(Fore.YELLOW + "WARN: [{}] not found in JSON: ({})".format(name, node) + Fore.RESET, file=sys.stderr)
        return value
        
    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print(Fore.RED + "IOTHUB_E2E_CONNECTION_STRING not set in environment" + Fore.RESET, file=sys.stderr)
            sys.exit(1)
        return service_connection_string

    def create_iot_device(self, connect_string, device_name):
        dev_connect = ""
        try:
            helper = Helper(connect_string)
            helper.create_device(device_name)
            print("create_iot_device: ({}) returned: ({})".format(device_name, 'OK'))
            dev_connect = helper.get_device_connection_string(device_name)
        except:
             print(Fore.RED + "Exception creating device: " + device_name, file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)

        return dev_connect
       
    def create_device_module(self, connect_string, device_name, module_name):
        mod_connect = None
        try:
            helper = Helper(connect_string)
            helper.create_device_module(device_name, module_name)
            print("create_device_module: ({}/{}) returned: ({})".format(device_name, module_name, 'OK'))
            mod_connect = helper.get_module_connection_string(device_name, module_name)
        except:
             print(Fore.RED + "Exception creating device: {}/{}".format(device_name, module_name), file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)
        return mod_connect

    def get_random_num_string(self, maxval):
        from random import randrange
        randnum = randrange(maxval)
        return str(randnum).zfill(len(str(maxval)))        

    def get_deployment_model_json(self, json_filename):
        json_manifest = ''
        try:
            with open(json_filename, 'r') as f:
                json_manifest = json.loads(f.read())
        except:
            print(Fore.RED + "ERROR: in JSON manifest: " + json_filename, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)
        return json_manifest

class DeviceObject:
    def __init__ (self, objectName, objectType='', apiSurface='', adapterName='', tcpPort='', deviceId='', connectionString=''):
        self.objectName       = objectName
        self.objectType       = objectType
        self.apiSurface       = apiSurface
        self.adapterName      = adapterName
        self.tcpPort          = tcpPort
        #self.deviceId         = deviceId
        self.connectionString = connectionString

class DeploymentObject:  
    def __init__ (self, deployment_name, identities=None, deployment_containers=None):
        self.deployment_name  = deployment_name
        self.containers       = deployment_containers
        self.identities = identities

if __name__ == "__main__":
    horton_create_devices = HortonCreateIdentities(sys.argv[1:])
