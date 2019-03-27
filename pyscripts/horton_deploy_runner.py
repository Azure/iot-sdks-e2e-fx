#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_deploy_runner.py
# author:   v-greach@microsoft.com 

import sys
import os
import json
import shutil
import pathlib
import traceback
from colorama import init, Fore, Back, Style

from horton_set_image_params import HortonSetImageParams
from horton_create_identities import HortonCreateIdentities
from horton_create_containers import HortonCreateContainers

class DeployHorton:

    def __init__(self, args):

        init(convert=True)
        home_dir = self.get_home_path()
        input_manifest_file = home_dir + "/horton/iothub_module_and_device.json"
        save_manifest_file  = home_dir + "/horton/deployment_template.json"

        try:
            base_dir = os.path.dirname(save_manifest_file)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
            cwd = self.norm_path(os.path.dirname(os.path.realpath(__file__)))
            shutil.copy(cwd + "/iothub_module_and_device.json", input_manifest_file)
            shutil.copy(input_manifest_file, save_manifest_file)
        except:
            print(Fore.RED + "Exception copying file: " + input_manifest_file, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)

        HortonSetImageParams(
            save_manifest_file, 
            'testObject', 
            "iotsdke2e.azurecr.io/pythonpreview-e2e-v2:vsts-14334",
            '"HostConfig": {"PortBindings": {"8080/tcp": [{"HostPort": "8071"}],"22/tcp": [{"HostPort": "8171"}]},"CapAdd": "SYS_PTRACE"}')

        HortonCreateIdentities(save_manifest_file)

        HortonCreateContainers(save_manifest_file)

        print("Complete")
        exit(0)

    def get_home_path(self):
        home_dir = str(pathlib.Path.home())
        from os.path import expanduser
        home_dir = expanduser("~")
        home_dir = os.path.normpath(home_dir)
        return self.norm_path(home_dir)

    def norm_path(self, file_path):
        file_path = file_path.replace('\\', '/')
        if ':/' in file_path:
            file_path = file_path[2:]
        return file_path

"""
Uber script:

1. copy template json to place where it can be modified
    cp iothub_module_and_device.json deployment_template.json
2. call script to set image name and createOptions
    python ./horton_set_image_params.py deployment_template.json testObject image "iotsdke2e.azurecr.io/pythonpreview-e2e-v2:vsts-14334"
    python ./horton_set_image_params.py deployment_template.json serviceObject image "iotsdke2e.azurecr.io/edge-e2e-node6:latest"
    python ./horton_set_image_params.py deployment_template.json serviceObject createOptions '"HostConfig": {"PortBindings": {"8080/tcp": [{"HostPort": "8071"}],"22/tcp": [{"HostPort": "8171"}]},"CapAdd": "SYS_PTRACE"}'
4. call script to create identities:
    python ./horton_create_identities.py deployment_template.json
3. call script to create containers
    python ./horton_create_containers.py deployment_template.json

--- run test ---

4. call script to remove identities
    python ./horton_delete_identities.py deployment_template.json
"""

if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])

