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
import time
import argparse
from colorama import init, Fore, Back, Style
from horton_set_image_params  import HortonSetImageParams
from horton_create_identities import HortonCreateIdentities
from horton_create_containers import HortonCreateContainers
from horton_delete_identities import HortonDeleteIdentities

class DeployHortonIdsAndContainers:
    def __init__(self, args):
        init(autoreset=True)
        parser = argparse.ArgumentParser(description='Runner to create devices, modules and containers for Horton')
        parser.add_argument('--manifest_template', required=True, help='filename of manifest template', type=str)
        parser.add_argument('--save_manifest', required=True, help='filename to save modifications', type=str)
        arguments = parser.parse_args()

        input_manifest_file = arguments.manifest_template
        save_manifest_file = arguments.save_manifest

        try:
            shutil.copy(input_manifest_file, save_manifest_file)
        except:
            print(Fore.RED + "Exception copying file: " + input_manifest_file, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)

        set_params = False
        if set_params:
            HortonSetImageParams(
                save_manifest_file, 
                'iotEdge',
                'testModule',
                '{}/node-e2e-v3:lkg'.format(os.environ["IOTHUB_E2E_REPO_ADDRESS"]),
                'latest',
                123,
                789,
                '{"HostConfig": {"PortBindings": {"8080/tcp": [{"HostPort": ""}],"22/tcp": [{"HostPort": ""}]},"CapAdd": "SYS_PTRACE"}}')

        HortonCreateIdentities(save_manifest_file)

        HortonCreateContainers(save_manifest_file)

        # Run TESTS
        print(Fore.YELLOW + "Running TESTS.. (stub)")
        time.sleep(3)

        HortonDeleteIdentities(save_manifest_file)

        print(Fore.GREEN + "Completed.")

if __name__ == "__main__":
    horton_deploymnet = DeployHortonIdsAndContainers(sys.argv[1:])
