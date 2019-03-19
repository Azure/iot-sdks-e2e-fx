#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: deploy_horton.py
# author:   v-greach@microsoft.com
# created:  03/15/2019
# Rev: 03/18/2019 B

import sys
import os
import json
import shutil
from colorama import init, Fore, Back, Style
import iothub_service_client
from iothub_service_client import IoTHubRegistryManager, IoTHubRegistryManagerAuthMethod
from iothub_service_client import IoTHubDeviceStatus, IoTHubError

class DeployHorton:

    def __init__(self, args):

        az_devices = []
        az_device_names = []
        module_count = 0
        init(convert=True)

        save_manifest_file = "c:\\iot_testdata\\horton\\horton_updated_manifest.json"

        connect_string = self.get_env_connect_string()

        #TEST_TEST_TEST
        self.NUKE_ALL_DEVICES_IN_HUB(connect_string)

        base_hostname = "hortondeploytest"
        deployment_name = base_hostname + '-' + self.get_random_num_string(10000)
        print("Deploying Horton to: " + deployment_name)

        deployment_json = self.get_deployment_model_json()
        azure_ids = deployment_json['deployment']['azure_identities']
        for az_id_name in azure_ids:
            device_connectstring = ''
            children_modules = []
            children_names = []

            az_type = self.get_json_value(azure_ids, az_id_name, 'type')
            az_device_id_suffix = self.get_json_value(azure_ids, az_id_name, 'device_id_suffix')
            
            if(self.node_has_children(azure_ids, az_id_name)):
                children = azure_ids[az_id_name]['children']
                children_modules = []
                children_names = []
                for child in children:
                    child_type = self.get_json_value(children, child, 'type')
                    child_module_id = self.get_json_value(children, child, 'module_id')
                    child_docker_image =  self.get_json_value(children, child, 'docker_image')
                    child_docker_container= self.get_json_value(children, child, 'docker_container_name')
                    child_docker_args = self.get_json_value(children, child, 'docker_creation_args')
                    #TEST_TEST_TEST - NextLines:1
                    child_module_name = child_module_id + "_" + self.get_random_num_string(1000)

                    new_module = DeviceModuleObject(child_module_id, az_id_name, child_type, child_docker_image, child_docker_container, child_docker_args, '')
                    children_modules.append(new_module)
                    children_names.append(child_module_name)
            else:
                az_docker_image = self.get_json_value(azure_ids, az_id_name, 'docker_image')
                az_docker_container = self.get_json_value(azure_ids, az_id_name, 'docker_container_name')
                az_docker_args = self.get_json_value(azure_ids, az_id_name, 'docker_creation_args')

            # TEST_TEST_TEST  - NextLines:1
            az_id_name = 'aa' + az_id_name + "_" + self.get_random_num_string(100) + az_device_id_suffix
            
            if(az_type == 'iothub_device'):
                new_device = self.create_iot_device(connect_string, az_id_name)
                if(new_device):
                    device_connectstring = self.create_device_connectstring(connect_string, az_id_name, new_device.primaryKey)
            else:
                new_device = None

            az_device_names.append(az_id_name)
            child_module_objects = []
            for child_module in children_modules:
                if(child_module.module_type == 'iothub_module'):
                    new_module = self.create_device_module(connect_string, az_id_name, child_module.module_id)
                    if(new_module):
                        child_module.module_connect = self.create_module_connectstring(connect_string, az_id_name, child_module.module_id, new_module.primaryKey)
                        child_module_objects.append(child_module)
                        module_count += 1

            child_object = DeviceChildrenObject(children_names, children_modules)
            new_device_obj = IotDeviceObject(az_id_name, az_type, az_device_id_suffix, device_connectstring, az_docker_image, az_docker_container, az_docker_args)
            new_device_obj.children = child_object
            az_devices.append(new_device_obj)

        print(Fore.GREEN + "Created {} Devices and {} Modules".format(len(az_devices), module_count))

        # add device id's and connection strings back to horton_manifest & save it
        new_az_id_obj = AzureIdObject(az_id_name, az_device_names, az_devices) 
        deployment_obj = DeploymentObject(deployment_name, new_az_id_obj)
        new_manifest_json = json.dumps(deployment_obj, default = lambda x: x.__dict__, sort_keys=False, indent=2)
        print(Fore.RESET + new_manifest_json)

        try:
            with open(save_manifest_file, 'w') as f:
                f.write(new_manifest_json)
        except:
            print(Fore.RED + "ERROR: writing JSON manifest to: " + save_manifest_file, file=sys.stderr)
            print(Fore.RESET + " ", file=sys.stderr)

        print("PHASE1 Complete")

        self.start_docker_containers(deployment_obj)

        print("DONE")

    def start_docker_containers(self, deployment_obj):
        from os.path import dirname, join, abspath
        sys.path.insert(0, abspath(join(dirname(__file__), '../horton_helpers')))
        from containers import all_containers

        for cntr in all_containers:
            print(cntr)

        deployment_devices = deployment_obj.azure_identities

        for device in deployment_devices:
            print("DeviceName: " + device)

        # PHASE 2: create containers
        #
        # read updated horton_manifest
        # docker login
        # for each docker container, 
        # a. fetch the image, fail if it's missing.
        # b. start it using args and the container_name,
        # c. use ensure_container.py to make sure it's responding.
        #
        # a & c will be used for edgehub deployments eventually

        return

    #####################
    ### INTERNAL ONLY ###
    #####################
    def NUKE_ALL_DEVICES_IN_HUB(self, conn_string):
        print(Fore.RED + "######################################")
        print(conn_string)
        code = input("Enter the secret code to NUKE ALL DEVICES: ")
        if(code == 'WtF'):
            print('NUKING ' + conn_string)

        sys.exit(1)

    def node_has_children(self, json, node):
        try:
            children = json[node]['children']
            if(children):
                return True
            else:
                return False
        except:
            return False

    def get_json_value(self, json, node, name):
        value = ""
        try:
            value = json[node][name]
        except:
            print(Fore.YELLOW + "ERROR: value not found in JSON: " + name, file=sys.stderr)
            print(Fore.RESET + " ", file=sys.stderr)
        return value
        
    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print(Fore.RED + "IOTHUB_E2E_CONNECTION_STRING not set in environment", file=sys.stderr)
            print(Fore.RESET + " ", file=sys.stderr)
            sys.exit(1)
        return service_connection_string

    def create_iot_device(self, connect_string, device_name):
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        new_device = None
        try:
            iothub_registry_manager = IoTHubRegistryManager(connect_string)
            new_device = iothub_registry_manager.create_device(device_name, "", "", auth_method)
        except Exception as e:
            print(Fore.RED + "Exception Creating device: " + device_name, file=sys.stderr)
            print(Fore.RED + str(e), file=sys.stderr)
            print(Fore.RESET + " ", file=sys.stderr)
        return new_device

    def create_device_module(self, connect_string, device_id, module_name):
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        new_module = None
        try:
            iothub_registry_manager = IoTHubRegistryManager(connect_string)
            new_module = iothub_registry_manager.create_module(device_id, '', '', module_name, auth_method)
        except Exception as e:
            print(Fore.RED + "Exception Creating device/module: " + module_name, file=sys.stderr)
            print(Fore.RED + e, file=sys.stderr)
            print(Fore.RESET + " ", file=sys.stderr)
        return new_module

    def create_device_connectstring(self, hub_connectstring, device_name, access_key):
        connect_parts = hub_connectstring.split(';')
        device_connectstring = "{};DeviceId={};SharedAccessKey={}".format(connect_parts[0], device_name, access_key)
        return device_connectstring

    def create_module_connectstring(self, hub_connectstring, device_name, module_name, access_key):
        connect_parts = hub_connectstring.split(';')
        device_connectstring = "{};DeviceId={};ModuleId={};SharedAccessKey={}".format(connect_parts[0], device_name, module_name, access_key)
        return device_connectstring

    def get_random_num_string(self, maxval):
        from random import randrange
        randnum = randrange(maxval)
        return str(randnum).zfill(len(str(maxval)))        

    def get_deployment_model_json(self):
        json_template = """{
            "deployment": {
                "azure_identities": {
                    "device_123": {
                        "type": "iothub_device",
                        "device_id_suffix": "_testdevice",
                        "docker_image": "blah",
                        "docker_container_name": "test_device",
                        "docker_creation_args": "-p 8081/tcp:80"
                    },
                    "helper_object": {
                        "type": "container",
                        "device_id_suffix": "_testdevice",
                        "docker_image": "blah",
                        "docker_container_name": "service_module",
                        "docker_creation_args": "-p 8081/tcp:80"
                    },
                    "device_456": {
                        "type": "iothub_device",
                        "device_id_suffix": "_device_with_module_children",
                        "children": {
                            "module1": {
                                "type": "iothub_module",
                                "module_id": "module1",
                                "docker_image": "docker_image/blah",
                                "docker_container_name": "module_under_test",
                                "docker_creation_args": "-p 8083/tcp:80"
                            },
                            "module2": {
                                "type": "iothub_module",
                                "module_id": "module2",
                                "docker_container_name": "other_module",
                                "docker_image": "docker_image/blah",
                                "docker_creation_args": "-p 8083/tcp:80"
                            }
                        }
					}
				}
			}
        }"""
        data = json.loads(json_template)
        return data

class DeviceModuleObject:  
    def __init__ (self, module_id, device_name='', module_type='', module_image='', module_contianer='', module_arguments='', module_connect=''):
        self.module_id        = module_id
        self.device_name      = device_name
        self.module_type      = module_type
        self.module_image     = module_image
        self.module_contianer = module_contianer
        self.module_arguments = module_arguments
        self.module_connect   = module_connect

class IotDeviceObject:  
    def __init__ (self, device_name='', device_type='', device_id_suffix='', device_connect='', docker_image='', docker_container='', docker_args='', children=None):
        self.device_name      = device_name
        self.device_type      = device_type
        self.device_id_suffix = device_id_suffix
        self.device_connect   = device_connect
        self.docker_image     = docker_image
        self.docker_container = docker_container
        self.docker_args      = docker_args
        self.children         = children

class DeploymentObject:  
    def __init__ (self, deployment_name, azure_identities=None):
        self.deployment_name  = deployment_name
        self.azure_identities = azure_identities

class AzureIdObject:  
    def __init__ (self, azure_devices=None, ks=[], vs=[]):
        self.azure_identities = azure_devices
        self.__dict__ = dict(zip(ks, vs))

class DeviceChildrenObject:  
    def __init__ (self, ks=[], vs=[]):
        self.__dict__ = dict(zip(ks, vs))

if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])
