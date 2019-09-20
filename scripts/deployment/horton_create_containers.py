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
import time
import requests
import argparse
from pprint import pprint
from colorama import init, Fore, Back, Style

class HortonCreateContainers:
    def __init__(self, args):
        self.horton_create_containers(args)

    def horton_create_containers(self, manifest_name):
        init(autoreset=True)
        manifest_json = self.get_deployment_model_json(manifest_name)
        deployment_containers = manifest_json['containers']

        for container in deployment_containers:
            self.create_and_start_container(deployment_containers[container])

    def create_and_start_container(self, container):
        auth_config = {
            "username": os.environ["IOTHUB_E2E_REPO_USER"],
            "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        }
        if sys.platform == 'win32':
            base_url = "tcp://127.0.0.1:2375"
        else:
            base_url = "unix://var/run/docker.sock"
            
        image_progress = 0
        cid = ''
        container_id = ''
        docker_image = container['image']
        docker_tag = container['imageTag']
        image_path = "{}:{}".format(docker_image, docker_tag)
        api_client = docker.APIClient(base_url=base_url)

        try:
            print("Pulling: {}".format(image_path))
            for _ in api_client.pull(docker_image, docker_tag, stream=True, auth_config=auth_config):
                self.progress(image_progress, status="Pulling: {}".format(image_path))
                image_progress += 1
            time.sleep(2)
        except docker.errors.APIError as e:
            if e.response.status_code == 500: #Internal Server Error
                print("Removing: " + image_path)
                api_client.remove_image(image_path)
                print("Pulling: {}".format(image_path))
                for _ in api_client.pull(docker_image, docker_tag, stream=True, auth_config=auth_config):
                    self.progress(image_progress, status="Pull: {}".format(image_path))
                    image_progress += 1
            else:
                print(Fore.RED + "Exception from Docker_Api_Client.pull({})".format(image_path), file=sys.stderr)
                traceback.print_exc()
                sys.exit(-1)
        try:
            container_name = container['name']
            host_config = None
            print("Creating Container for: " + container_name)
            if 'createOptions' in container:
                if 'HostConfig' in container['createOptions']:
                    opts_json = container['createOptions']['HostConfig']
                    ports = opts_json['PortBindings']
                    host_config = api_client.create_host_config(port_bindings=ports)
            try:
                if host_config:
                    container_id = api_client.create_container(
                        image_path, 
                        name=container_name, host_config=host_config)
                else:
                    container_id = api_client.create_container(
                        image_path, 
                        name=container_name)
            except docker.errors.APIError as e:
                if e.response.status_code == 409: #Container_Exists
                    try:
                        cid = self.get_cid_from_container_name(api_client.containers(all=True), container_name)
                        print(Fore.YELLOW + "Stopping container: " + container_name, file=sys.stderr) 
                        api_client.stop(cid)
                        print(Fore.YELLOW + "Removing container: " + container_name, file=sys.stderr) 
                        api_client.remove_container(container_name, force=True)
                    except:
                        print(Fore.RED + "Exception from Docker_Api_Client create/remove container: " + container_name, file=sys.stderr)
                        traceback.print_exc()
                        sys.exit(-1)
                    print("Retrying Creating Container for: " + container_name)
                    container_id = api_client.create_container(
                        image_path, 
                        name=container_name, 
                        host_config=host_config)
                else:
                    print(Fore.RED + "Exception from Docker_Api_Client create container: " + container_name, file=sys.stderr)
                    traceback.print_exc()
                    sys.exit(-1)
            try:
                cid = container_id['Id']
                cname = self.get_container_name_from_cid(api_client.containers(all=True), cid)
                print(Fore.GREEN + "Created Container: " + cname)
                print("Starting Container: " + cname)
                api_client.start(container=cid)
                time.sleep(5)
                self.ensure_container(api_client, container_name)
            except:
                print(Fore.RED + "Exception from Docker_Api_Client.START: " + cid, file=sys.stderr)
                traceback.print_exc()
                sys.exit(-1)
        except:
            print(Fore.RED + "Exception from Docker_Api_Client.create_container: " + container_name, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)

    def ensure_container(self, api_client, container_name):
        containers = api_client.containers(all=True)
        container = self.get_container_by_name(containers, container_name)
        if not container:
            print(Fore.YELLOW + "Container {} is not deployed".format(container_name))
            return
        if container['State'] != 'running':
            print(Fore.YELLOW + "Container {} is not Running".format(container_name))

        restart_attempts = 10
        container_startup_time = 5

        for f in range(0, restart_attempts):
            try:
                for port in container['Ports']:
                    if 'PublicPort' in port:
                        host_port =  port['PublicPort']
                        uri = "http://localhost:{}/wrapper/message".format(host_port)
                        body = {"msg": "test message {} from ensure_container".format(f)}
                        print("Sending {} to {}".format(json.dumps(body), uri))
                        r = requests.put(uri, json=body)
            except Exception as e:
                print(Fore.YELLOW + "Container {} is not responding".format(container_name), file=sys.stderr)
                print(str(e))
            else:
                print(Fore.GREEN + "Container {} is running and responding".format(container_name))
                #pprint(r.__dict__)
                return

            print(Fore.YELLOW + "restarting container {}".format(container_name), file=sys.stderr)
            try:
                api_client.restart(container)
                time.sleep(container_startup_time)
            except:
                print(Fore.RED + "Exception from Docker_Api_Client.Restart: " + container_name, file=sys.stderr)
                traceback.print_exc()
        print(Fore.RED + "Container {} did not respond after {} restart attempts".format(
                container_name, restart_attempts))

    def get_container_by_name(self, containers, container_name):
        container = None
        for container in containers:
            ctr_names = container.get('Names')
            for ctr_name in ctr_names:
                ctr_name = ctr_name.strip('/')
                if container_name == ctr_name:
                    return container
        return container

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

    def get_container_name_from_cid(self, containers, cid):
        container_name = ''
        for ctr in containers:
            if cid == ctr.get('Id'):
                ctr_names = ctr.get('Names')
                for ctr_name in ctr_names:
                    ctr_name = ctr_name.strip('/')
                    container_name = ctr_name
                    return container_name
        return container_name

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

    def get_tick(self, val, min, max):
        ticks = ['*', '\\', '|', '/', '-']
        t_ret = 'o'
        p = max - min + 1
        mod = (val - min) % p
        if(mod < 0):
            mod += p
        t = (min + mod)
        if (t >= 0 and t <= max):
            t_ret = ticks[t]
        return t_ret

    def progress(self, count, status=''):
        sys.stdout.write('[%s] %s ...%s\r' % (self.get_tick(count, 1, 4), count, status))
        sys.stdout.flush()

    def get_random_num_string(self, maxval):
        from random import randrange
        randnum = randrange(maxval)
        return str(randnum).zfill(len(str(maxval)))        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Runner to create and run containers for Horton')
    parser.add_argument('--manifest', required=True, help='path and filename of manifest', type=str)
    arguments = parser.parse_args()
    horton_containers = HortonCreateContainers(arguments.manifest)
