#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_create_containers.py
# author:   v-greach@microsoft.com

import sys
import os
import json
import traceback
import docker
from colorama import init, Fore, Back, Style

class HortonCreateContainers:

    def __init__(self, manifest_name):
        init(convert=True)
        self.horton_create_identities(manifest_name)

    def horton_create_identities(self, manifest_name):
        manifest_json = self.get_deployment_model_json(manifest_name)
        deployment_containers = manifest_json['containers']
        for container in deployment_containers:
            self.create_container(container)

    def create_container(self, container):
        print(container)
        repo_name =  os.environ["IOTHUB_E2E_REPO_ADDRESS"]
        #client = docker.from_env()
        #acr_url = "tcp://127.0.0.1:2376"
        acr_url = "tcp://127.0.0.1:2376"
        repo_port = ":2376"
        #acr_url = "tcp://" + repo_name + repo_port
        api_client = docker.APIClient(base_url=acr_url, tls=True)

        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        auth_config = {
            "username": os.environ["IOTHUB_E2E_REPO_USER"],
            "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        }


        try:
            #container = client.containers.get(container_name)
            ret = api_client.login(repo_user, repo_password)
            ret = api_client.pull(
                    "iotsdke2e.azurecr.io/edge-e2e-node6",
                    "latest",
                    auth_config=auth_config)
        except:
             print(Fore.RED + "Exception from Docker_Api_Client: " + acr_url, file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)

    def get_deployment_model_json(self, json_filename):
        json_manifest = ''
        try:
            with open(json_filename, 'r') as f:
                json_manifest = json.loads(f.read())
        except:
            print(Fore.RED + "ERROR: in JSON manifest: " + json_filename + Fore.RESET, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)
        return json_manifest

if __name__ == "__main__":
    horton_create_containers = HortonCreateContainers(sys.argv[1:])

