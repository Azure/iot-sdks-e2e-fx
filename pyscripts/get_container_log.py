#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_create_containers.py
# author:   v-greach@microsoft.com

import sys
import os
#import json
#import traceback
import docker
#import time
#import requests
import argparse
#from pprint import pprint
#from colorama import init, Fore, Back, Style

class HortonGetContainerLog:
    def __init__(self, args):
        self.get_container_log(args)

    def get_container_log(self, container_name):
        #auth_config = {
        #    "username": os.environ["IOTHUB_E2E_REPO_USER"],
        #    "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        #}
        if sys.platform == 'win32':
            base_url = "tcp://127.0.0.1:2375"
        else:
            base_url = "unix://var/run/docker.sock"
            
        api_client = docker.APIClient(base_url=base_url)
        containers = api_client.containers(all=True)
        container = self.get_container_by_name(containers, container_name)
        #if not container:
        #    print(Fore.YELLOW + "Container {} is not deployed".format(container_name))
        #    return
        #if container['State'] != 'running':
        #    print(Fore.YELLOW + "Container {} is not Running".format(container_name))

        log = api_client.logs(container, stdout=True, stderr=True, stream=False, timestamps=True,)

        #for line in log:
        #    print(line)
        print(line)


    def get_container_by_name(self, containers, container_name):
        container = None
        for container in containers:
            ctr_names = container.get('Names')
            for ctr_name in ctr_names:
                ctr_name = ctr_name.strip('/')
                if container_name == ctr_name:
                    return container
        return container

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get docker log for container')
    parser.add_argument('--container', required=True, help='path and filename of manifest', type=str)
    arguments = parser.parse_args()
    horton_containers = HortonGetContainerLog(arguments.container)
