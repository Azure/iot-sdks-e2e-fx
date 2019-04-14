#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_delete_identities.py
# author:   v-greach@microsoft.com

import sys
import os
import json
import pathlib
import docker
import traceback
import argparse
from colorama import init, Fore, Back, Style
from service_helper import Helper

class HortonDeleteIdentities:
    def __init__(self, args):
        self.horton_delete_identities_and_containers(args)

    def horton_delete_identities_and_containers(self, save_manifest_file):
        init(autoreset=True)
        print(Fore.GREEN + "Deleting Devices/Modules/Containers in IotHub and Docker from: {}".format(save_manifest_file))
        deployment_json = self.get_deployment_model_json(save_manifest_file)
        hub_connect_string = self.get_env_connect_string()
        helper = Helper(hub_connect_string)
        try:
            identity_json = deployment_json['containers']
            for containers in identity_json:
                container_json = identity_json[containers]
                container_name = container_json['name']
                self.delete_container(container_name)
        except:
            print(Fore.RED + "Exception Processing HortonManifest Containers: " + save_manifest_file, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)
        try:
            identity_json = deployment_json['identities']
            for azure_device in identity_json:
                device_json = identity_json[azure_device]
                objectType = device_json['objectType']
                if objectType in ["iothub_device", "iotedge_device"]:
                    device_id = device_json['deviceId']
                    print("deleting device {}".format(device_id))
                    helper.try_delete_device(device_id)
        except:
            print(Fore.RED + "Exception Processing HortonManifest Identities: " + save_manifest_file, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)
        return True

    def delete_container(self, container_name):
        if sys.platform == 'win32':
            base_url = "tcp://127.0.0.1:2375"
        else:
            base_url = "unix://var/run/docker.sock"

        api_client = docker.APIClient(base_url=base_url)
        containers = api_client.containers(all=True)
        for container in containers:
            ctr_names = container.get('Names')
            for ctr_name in ctr_names:
                ctr_name = ctr_name.strip('/')
                if container_name == ctr_name:
                    try:
                        cid = self.get_cid_from_container_name(containers, container_name)
                        print("Stopping container: " + container_name, file=sys.stderr) 
                        api_client.stop(cid)
                        print("Removing container: " + container_name, file=sys.stderr) 
                        api_client.remove_container(container_name)
                    except:
                        print(Fore.RED + "ERROR: stopping/removing container: " + ctr_name, file=sys.stderr)
                        traceback.print_exc()
                        sys.exit(-1)

    def get_cid_from_container_name(self, containers, container_name):
        cid = ''
        for ctr in containers:
            cid = ctr.get('Id')
            ctr_names = ctr.get('Names')
            for ctr_name in ctr_names:
                ctr_name = ctr_name.strip('/')
                if container_name == ctr_name:
                    return cid
        return cid

    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print(Fore.RED + "IOTHUB_E2E_CONNECTION_STRING not set in environment", file=sys.stderr)
            sys.exit(-1)
        return service_connection_string

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
    parser = argparse.ArgumentParser(description='Runner to delete devices, modules and containers for Horton')
    parser.add_argument('--manifest', required=True, help='path and filename of manifest', type=str)
    arguments = parser.parse_args()
    horton_delete = HortonDeleteIdentities(arguments.manifest)
