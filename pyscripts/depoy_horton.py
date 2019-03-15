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

        print("Deploying Horton")

        deployment_json = self.get_deployment_model_json()

        rndval = self.get_random_num_string(10000)

        print(rndval)

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
                                "docker_image": "docker_image/blah"
                            }
                        }
					}
				}
			}
        }"""

        data = json.loads(json_template)
        #if data["fa"] == "cc.ee":
        #    data["fb"]["new_key"] = "cc.ee was present!"

        return json.dumps(data)


if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])


