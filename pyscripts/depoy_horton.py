#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: deploy_horton.py
# author:   v-greach@microsoft.com
# created:  03/15/2019
# Rev: 03/17/2019 F

import sys
import os
import json
import shutil
import iothub_service_client
from iothub_service_client import IoTHubRegistryManager, IoTHubRegistryManagerAuthMethod
from iothub_service_client import IoTHubDeviceStatus, IoTHubError

class DeployHorton:

    def __init__(self, args):

        az_devices = []
        module_children = []
        connect_string = self.get_env_connect_string()
        base_hostname = "hortondeploytest"
        deployment_name = base_hostname + '-' + self.get_random_num_string(10000)
        print("Deploying Horton to: " + deployment_name)

        deployment_json = self.get_deployment_model_json()
        azure_ids = deployment_json['deployment']['azure_identities']
        for az_id_name in azure_ids:
            az_type = self.get_json_value(azure_ids, az_id_name, 'type')
            az_device_id_suffix = self.get_json_value(azure_ids, az_id_name, 'device_id_suffix')
            
            print(az_id_name)
            print("type: " + az_type)
            print("device_id_suffix: " + az_device_id_suffix)

            if(self.node_has_children(azure_ids, az_id_name)):
                children = azure_ids[az_id_name]['children']
                module_children = []
                for child in children:
                    child_type = self.get_json_value(children, child, 'type')
                    child_module_id = self.get_json_value(children, child, 'module_id')
                    child_docker_image =  self.get_json_value(children, child, 'docker_image')
                    child_docker_container= self.get_json_value(children, child, 'docker_container_name')
                    child_docker_args = self.get_json_value(children, child, 'docker_creation_args')
                    #TEST_TEST_TEST - NextLines:1
                    child_module_name = child_module_id + "_" + self.get_random_num_string(1000)

                    new_module = DeviceModuleObject(None, child_module_name, child_type, child_module_id, child_docker_image, child_docker_container, child_docker_args)
                    module_children.append(new_module)

                    print("...." + child)
                    print("........type: " + child_type)
                    print("........module_name: " + child_module_name)
                    print("........module_id: " + child_module_id)
                    print("........docker_image: " + child_docker_image)
                    print("........docker_container_name: " + child_docker_container)
                    print("........docker_creation_args: " + child_docker_args)
            else:
                az_docker_image = self.get_json_value(azure_ids, az_id_name, 'docker_image')
                az_docker_container = self.get_json_value(azure_ids, az_id_name, 'docker_container_name')
                az_docker_args = self.get_json_value(azure_ids, az_id_name, 'docker_creation_args')
                
                print("docker_image: " + az_docker_image)
                print("docker_container_name: " + az_docker_container)
                print("docker_creation_args: " + az_docker_args)

            # TEST_TEST_TEST  - NextLines:1
            az_id_name = az_id_name + "_" + self.get_random_num_string(100) + az_device_id_suffix
            new_device = self.create_iot_device(connect_string, az_id_name)

            child_module_objects = []
            for child_module in module_children:
                new_module = self.create_device_module(connect_string, az_id_name, child_module.module_name)
                child_module_objects.append(new_module)

            new_device_obj = IotDeviceObject(new_device, az_id_name, az_device_id_suffix, az_docker_image, az_docker_container, az_docker_args)
            new_device_obj.modules = child_module_objects
            az_devices.append(new_device_obj)

        print(az_devices)

        # add device id's and connection strings back to horton_manifest & save it


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
            print("ERROR: value not found in JSON: " + name)
        return value
        
    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print("IOTHUB_E2E_CONNECTION_STRING not set in environment")
            sys.exit(1)
        return service_connection_string

    def create_iot_device(self, connect_string, device_name):
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        new_device = None
        try:
            iothub_registry_manager = IoTHubRegistryManager(connect_string)
            new_device = iothub_registry_manager.create_device(device_name, "", "", auth_method)
        except Exception as e:
            print("Exception Creating device: " + device_name, file=sys.stderr)
            print(e, file=sys.stderr)
        return new_device

    def create_device_module(self, connect_string, device_id, module_name):
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        new_module = None
        try:
            iothub_registry_manager = IoTHubRegistryManager(connect_string)
            new_module = iothub_registry_manager.create_module(device_id, '', '', module_name, auth_method)
        except Exception as e:
            print("Exception Creating device/module: " + module_name, file=sys.stderr)
            print(e, file=sys.stderr)
        return new_module

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
    def __init__ (self, module_obj=None, mod_name='', mod_type='', mod_id='', mod_img='', mod_ctr='', mod_args=''):
        self.module_obj       = module_obj
        self.module_name      = mod_name
        self.module_type      = mod_type
        self.module_id        = mod_id
        self.module_image     = mod_img
        self.module_contianer = mod_ctr
        self.module_arguments = mod_args

class IotDeviceObject:  
    def __init__ (self, device_obj, device_name='', device_id_suffix='', docker_image='', docker_container='', docker_args=''):
        self.device_obj       = device_obj
        self.device_name      = device_name
        self.device_id_suffix = device_id_suffix
        self.docker_image     = docker_image
        self.docker_container = docker_container
        self.docker_args      = docker_args
        self.modules          = None

if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])
