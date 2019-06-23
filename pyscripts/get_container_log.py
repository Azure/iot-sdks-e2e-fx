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


        log_blob = api_client.logs(container, stdout=True, stderr=True, stream=False, timestamps=True,)
        
        #log_blob = [123, 49, 58, 32, 39, 97, 39, 44, 32, 50, 58, 32, 39, 98, 39, 44, 32, 51, 58, 32, 39, 99, 39, 125]  
        #log_blob = bytearray(b'aabbqwerty\n20trythistestdatafor\nnow20and\n20')
        #log_blob = b'aabbqwerty\n20trythistestdatafor\n20now20and\n20x333'

        log_blob_len = len(log_blob)
        log_blob_pos = -1
        log_blob_last_pos = 0
        log_delimiter = b"\n20"
        log_delimiter_len = len(log_delimiter)
        log_lines = []
        for _ in range(0, log_blob_len):
            delimeter_match = False
            log_blob_pos += 1
            if log_blob_pos + log_delimiter_len < log_blob_len:
                for i in range(0, log_delimiter_len):
                    if log_blob[i + log_blob_pos] != log_delimiter[i]:
                        break
                    if i == log_delimiter_len - 1:
                        delimeter_match = True
            if delimeter_match:
                bin_buffer = ""
                for b in range(log_blob_last_pos, log_blob_pos):
                    if log_blob[b] > 127:
                        bin_buffer += "#"
                    else:
                        bin_buffer += chr(log_blob[b])
                log_blob_last_pos = log_blob_pos + log_delimiter_len
                log_blob_pos = log_blob_last_pos
                log_lines.append(bin_buffer)
                delimeter_match = False

        if log_blob_last_pos < log_blob_len:
            bin_buffer = ""
            for b in range(log_blob_last_pos, log_blob_len):
                bin_buffer += chr(log_blob[b])
            log_lines.append(bin_buffer)

        for line in log_lines:
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
