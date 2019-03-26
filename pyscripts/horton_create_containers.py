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
            self.create_container(deployment_containers[container])

    def create_container(self, container):
        print(container)
        repo_name =  os.environ["IOTHUB_E2E_REPO_ADDRESS"]
        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        auth_config = {
            "username": os.environ["IOTHUB_E2E_REPO_USER"],
            "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        }

        print(container)
        #docker_image = "iotsdke2e.azurecr.io/edge-e2e-node6:latest"
        docker_image = container['image']

        try:
            self.pull_docker_image(docker_image)
        except:
             print(Fore.RED + "Exception from Docker_Api_Client: " + docker_image, file=sys.stderr)
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

    def pull_docker_image(self, image_path):
        docker_exe = 'docker.exe'
        docker_cmd = 'pull ' + image_path
        self.run_shell_command(docker_exe + " " + docker_cmd)

    def run_shell_command(self, cmd_to_run):
        import subprocess
        home_path = self.get_home_path()
        run_path = home_path + '/run_cmd.bat'
        print(run_path)
        try:
            with open(run_path, 'w') as f:
                f.write(cmd_to_run + '\n')
            subprocess.call(run_path) 
        except:
            print(Fore.RED + "ERROR: creating file: " + run_path + Fore.RESET, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)

    def get_home_path(self):
        import pathlib
        home_dir = str(pathlib.Path.home())
        from os.path import expanduser
        home_dir = expanduser("~")
        home_dir = os.path.normpath(home_dir)
        home_dir = home_dir.replace('\\', '/')
        if ':/' in home_dir:
            home_dir = home_dir[2:]
        return home_dir

if __name__ == "__main__":
    horton_create_containers = HortonCreateContainers(sys.argv[1:])

