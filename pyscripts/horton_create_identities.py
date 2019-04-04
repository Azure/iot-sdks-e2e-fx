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
import argparse
from colorama import init, Fore, Back, Style
from service_helper import Helper

class HortonCreateIdentities:
    def __init__(self, args):
        self.horton_create_identities(args)

    def horton_create_identities(self, save_manifest_file):
        init(autoreset=True)
        deployment_json = self.get_deployment_model_json(save_manifest_file)
        hub_connect_string = self.get_env_connect_string()
        id_prefix = "horton_{}_{}".format(self.get_random_num_string(1000),self.get_random_num_string(1000))
        device_count = 0
        module_count = 0
        try:
            identity_json = deployment_json['identities']
            for azure_device in identity_json:
                device_json = identity_json[azure_device]
                objectType = device_json['objectType']
                objectName = device_json['objectName']
                device_id = "{}_{}".format(id_prefix, objectName)
                if objectType == "iothub_device":
                    device_json['deviceId'] = device_id
                    device_json['connectionString'] = self.create_iot_device(hub_connect_string, device_id)
                    device_count += 1
                    if 'modules' in device_json:
                        modules = device_json['modules']
                        for module in modules:
                            module_json = modules[module]
                            module_json['moduleId']  = module
                            module_json['deviceId']  = device_id
                            module_json['connectionString']  = self.create_device_module(hub_connect_string, device_id, module)
                            deployment_json['identities'][azure_device][module] = module_json
                            module_count += 1
                elif objectType in ["iothub_service", "iothub_registry"]:
                    print("creating service {}".format(device_id))
                    device_json['connectionString'] = hub_connect_string
                    device_count += 1
                deployment_json['identities'][azure_device] = device_json
        except:
            print(Fore.RED + "Exception Processing HortonManifest: " + save_manifest_file, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)

        print(Fore.GREEN + "Created {} Devices and {} Modules".format(device_count, module_count))
        try:
            with open(save_manifest_file, 'w') as f:
                f.write(json.dumps(deployment_json, default = lambda x: x.__dict__, sort_keys=False, indent=2))
        except:
            print(Fore.RED + "ERROR: writing JSON manifest to: " + save_manifest_file, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)
        return True
        
    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print(Fore.RED + "IOTHUB_E2E_CONNECTION_STRING not set in environment", file=sys.stderr)
            sys.exit(-1)
        return service_connection_string

    def create_iot_device(self, connect_string, device_name):
        dev_connect = ""
        try:
            helper = Helper(connect_string)
            helper.create_device(device_name)
            dev_connect = helper.get_device_connection_string(device_name)
        except:
            print(Fore.RED + "Exception creating device: " + device_name, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)
        return dev_connect
       
    def create_device_module(self, connect_string, device_name, module_name):
        mod_connect = ""
        try:
            helper = Helper(connect_string)
            helper.create_device_module(device_name, module_name)
            mod_connect = helper.get_module_connection_string(device_name, module_name)
        except:
            print(Fore.RED + "Exception creating module: {}/{}".format(device_name, module_name), file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)
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
            sys.exit(-1)
        return json_manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create devices and modules for Horton')
    parser.add_argument('--manifest', required=True, help='path and filename of manifest', type=str)
    arguments = parser.parse_args()
    hortoncreate_indetities = HortonCreateIdentities(arguments.manifest)
