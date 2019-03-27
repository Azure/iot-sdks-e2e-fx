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
        repo_name =  os.environ["IOTHUB_E2E_REPO_ADDRESS"]
        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        auth_config = {
            "username": os.environ["IOTHUB_E2E_REPO_USER"],
            "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        }

        docker_image = container['image']

        #api_client = docker.APIClient(base_url='tcp://iotsdke2e.azurecr.io:2375')
        api_client = docker.APIClient(base_url='https://localhost:2375')
        try:
            print("Pulling: " + docker_image)
            #self.pull_docker_image(docker_image)
            #ret = api_client.pull(docker_image, '', stream=True, auth_config=auth_config)
        except:
             print(Fore.RED + "Exception from Docker_Api_Client.pull: " + docker_image, file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)

        try:
            container_name = container['name']
            print("Creating Container: " + container_name)
            create_opts = container['createOptions']

            container_id = api_client.create_container(
                docker_image, '', name=container_name, ports=[1111, 2222],
                host_config=api_client.create_host_config(port_bindings={
                    1111: 4567,
                    2222: None
                })
            )
            #Deprecation warning: Passing configuration options in start is no longer supported. Users are expected to provide host config options in the host_config parameter of create_container().
            try:
                ret = api_client.start(container=container.get(container_name))
                # ensure_container(container_name)
            except:
                print(Fore.RED + "Exception from Docker_Api_Client.start: " + container_name, file=sys.stderr)
                traceback.print_exc()
                print(Fore.RESET, file=sys.stderr)
        except:
             print(Fore.RED + "Exception from Docker_Api_Client.create_container: " + container_name, file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)

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

    def pull_docker_image(self, image_path):
        docker_exe = 'docker.exe'
        docker_cmd = 'pull ' + image_path
        self.run_shell_command(docker_exe + " " + docker_cmd)

    def run_shell_command(self, cmd_to_run):
        import subprocess
        home_path = self.get_home_path()
        run_path = home_path + '/horton/run_cmd.bat'
        print(run_path)
        try:
            with open(run_path, 'w') as f:
                f.write(cmd_to_run + '\n')
            subprocess.call(run_path) 
        except:
            print(Fore.RED + "ERROR: creating file: " + run_path, file=sys.stderr)
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

