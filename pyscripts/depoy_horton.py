#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: deploy_horton.py
# author:   v-greach@microsoft.com
# created:  03/15/2019
# Rev: 03/15/2019 A

import sys
import os
import json
from pprint import pprint
import shutil

class DeployHorton:

    def __init__(self, args):

        #base_hostname = "bertk-newvm-1"
        #base_hostname = "giothub333.azure-devices.net"
        #base_hostname = "greggiothub1.azure-devices.net"
        
        base_hostname = "hortondeploytest"
        deployment_name = base_hostname + '-' + self.get_random_num_string(10000)
        print("Deploying Horton to: " + deployment_name)

        deployment_json = self.get_deployment_model_json()
        azure_ids = deployment_json['deployment']['azure_identities']
        for id_name in azure_ids:
            print(id_name)
            print("type: " + self.get_json_value(azure_ids, id_name, 'type'))
            print("device_id_suffix: " + self.get_json_value(azure_ids, id_name, 'device_id_suffix'))

            if(self.node_has_children(azure_ids, id_name)):
                children = azure_ids[id_name]['children']
                for child in children:
                    print("...." + child)
                    print("........type: " + self.get_json_value(children, child, 'type'))
                    print("........module_id: " + self.get_json_value(children, child, 'module_id'))
                    print("........docker_image: " + self.get_json_value(children, child, 'docker_image'))
                    print("........docker_container_name: " + self.get_json_value(children, child, 'docker_container_name'))
                    print("........docker_creation_args: " + self.get_json_value(children, child, 'docker_creation_args'))
            else:
                print("docker_image: " + self.get_json_value(azure_ids, id_name, 'docker_image'))
                print("docker_container_name: " + self.get_json_value(azure_ids, id_name, 'docker_container_name'))
                print("docker_creation_args: " + self.get_json_value(azure_ids, id_name, 'docker_creation_args'))

        # STEP 1
        # read horton_manifest
        # basename = hostname + random number
        # walk the tree
        # create device & module identietes on azure
        # add device id's and connection strings back to horton_manifest & save it


        #Step 2: create containers
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
            return True
        except:
            return False

    def get_json_value(self, json, node, name):
        try:
            value = json[node][name]
            return value
        except:
            print("ERROR: value not found in JSON: " + name)
        return ""
        

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
        #if data["fa"] == "cc.ee":
        #    data["fb"]["new_key"] = "cc.ee was present!"

        #return json.dumps(data)
        return data


if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])


