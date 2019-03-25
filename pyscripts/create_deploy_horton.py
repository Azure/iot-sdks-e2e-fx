#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: deploy_horton.py
# author:   v-greach@microsoft.com
# created:  03/15/2019
# Rev: 03/25/2019 D

import sys
import os
import json
import shutil
import traceback
import base64
import urllib
import pathlib
from colorama import init, Fore, Back, Style
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '../horton_helpers')))
from service_helper import Helper

class DeployHorton:

    def __init__(self, args):

        init(convert=True)
        home_dir = str(pathlib.Path.home())
        from os.path import expanduser
        home_dir = expanduser("~")
        input_manifest_file = os.path.normpath(home_dir + "/horton/iothub_module_and_device.json")
        save_manifest_file = os.path.normpath(home_dir + "/horton/iothub_updated_module_and_device.json")

        self.create_hotron_devices_from_manifest(input_manifest_file, save_manifest_file)

        #self.setup_docker_containers(save_manifest_file)

    def setup_docker_containers(self, input_manifest_file):
        import urllib
        import base64
        import docker
        from os.path import dirname, join, abspath
        sys.path.insert(0, abspath(join(dirname(__file__), '../horton_helpers')))
        from containers import all_containers

        from docker_tags import DockerTags

        if not ("IOTHUB_E2E_REPO_ADDRESS" in os.environ
            and "IOTHUB_E2E_CONNECTION_STRING" in os.environ
            and "IOTHUB_E2E_REPO_USER" in os.environ
            and "IOTHUB_E2E_REPO_PASSWORD" in os.environ):
            print("Error: Docker container repository credentials are not set in IOTHUB_E2E_REPO* environment variables.")
            return

        e2e_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        repo_name =  os.environ["IOTHUB_E2E_REPO_ADDRESS"]
        repo_address = "https://" + repo_name
        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        auth_config = {
            "username": os.environ["IOTHUB_E2E_REPO_USER"],
            "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"],
        }

        deployment_json = self.get_deployment_model_json(input_manifest_file)
        identity_json = deployment_json['azure_identities']
        containers_needed = []
        for azure_device in identity_json:
            az_device_name = self.get_json_value(azure_device, 'device_name')
            docker_container = self.get_json_value(azure_device, "docker_container")
            if not (docker_container in containers_needed):
                containers_needed.append(docker_container)
            print("...." + az_device_name)
            children = azure_device['children']
            for child in children:
                child_module_id = self.get_json_value(child, 'module_id')
                docker_container = self.get_json_value(child, "module_docker_container_name")
                if not (docker_container in containers_needed):
                    containers_needed.append(docker_container)
                print("........" + child_module_id)

        containers_to_get = []
        for container in containers_needed:
            if(container in all_containers):
                containers_to_get.append(container)
            else:
                print("Requested container is not in all_containers: " + container)

        docker_repo_address = os.environ.get("IOTHUB_E2E_REPO_ADDRESS")
        docker_address = 'https://' + docker_repo_address
        docker_repo_name = 'node-e2e-v2'
        docker_tag = 'vsts-14244'

        docker_images = []    
        for container in containers_to_get:
            print("Getting container: " + container)

        docker_manifest = self.docker_get_manifest(docker_address, docker_repo_name, docker_tag)
        docker_image = self.docker_get_image(docker_address, docker_repo_name, docker_tag)
        print(docker_image)

        #api_client = None
        #try:
        #    api_client = docker.APIClient(base_url=docker_base, timeout=600)
        #except Exception as e:
        #     print(Fore.RED + "Exception connecting to Docker: " + docker_base, file=sys.stderr)
        #     traceback.print_exc()
        #     print(Fore.RESET, file=sys.stderr)

        #if not (api_client):
        #    try:
        #        docker_base = "unix://var/run/docker.sock"
        #        api_client = docker.APIClient(base_url=docker_base, timeout=600)
        #        print("APIClient: " + api_client)
        #    except Exception as e:
        #        print(Fore.RED + "Exception connecting to Docker: " + docker_base, file=sys.stderr)
        #        traceback.print_exc()
        #        print(Fore.RESET, file=sys.stderr)

        #image_path = '{}/edge-e2e-node6'.format(docker_repo)

        #try:
        #    for line in api_client.pull(image_path, 'latest', stream=True, auth_config=auth_config):
        #        print(line)
        #except Exception as e:
        #     print(Fore.RED + "Exception pulling from Docker: " + docker_base, file=sys.stderr)
        #     traceback.print_exc()
        #     print(Fore.RESET, file=sys.stderr)

        #try:
            #client = docker.DockerClient(base_url='192.168.65.1:53')
            #client = docker.DockerClient(base_url="unix://var/run/docker.sock")

            #client = docker.DockerClient(base_url=repo_connect, version='auto', timeout=120)
            #resp = client.login(username="iotsdke2e", password="H034BRLUTtNFHg8Sw0jiiX8Km8=uCHkn", dockercfg_path=config_file)

            #client = docker.DockerClient(base_url=repo_connect)
            #resp = client.login(username=repo_user, password=repo_password)

            #cntr_list = client.containers.list(all=True)

            #client.images.push('arycloud/istiogui', tag=deployment.name)
            #docker login repo_name
        #except Exception as e:
             #print(Fore.RED + "Exception connecting to Docker: " + hub_repo_connect, file=sys.stderr)
             #traceback.print_exc()
             #print(Fore.RESET, file=sys.stderr)
             #print(Fore.RESET, file=sys.stderr)


        # PHASE 2: create containers
        #
        # read updated horton_manifest
        # docker login
        # for each docker container, 
        # a. fetch the image, fail if it's missing.
        # b. start it using args and the container_name,
        # c. use ensure_container.py to make sure it's responding.
        #
        # a & c will be used for edgehub deployments eventually

        return True

    def docker_get_manifest(self, docker_address, docker_repo, repo_tag):
        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        auth_header = self.build_auth_header(repo_user, repo_password)
        repo_uri =  "{}/v2/{}/manifests/{}".format(docker_address, docker_repo, repo_tag)
        content_type = 'application/vnd.docker.distribution.manifest.v2+json'
        manifest = ''
        try:
            req = urllib.request.Request(repo_uri, method='GET')
            req.add_header('Authorization', auth_header)
            req.add_header('Accept', content_type)
            content = urllib.request.urlopen(req).read()
            manifest = content.decode('ascii')
        except Exception:
             print(Fore.RED + "Exception connecting to Docker: " + docker_address, file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)
        return manifest

    def docker_get_image(self, docker_address, docker_repo, repo_tag):
        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]
        auth_header = self.build_auth_header(repo_user, repo_password)
        content_type = 'application/vnd.docker.image.rootfs.diff.tar.gzip'

        #GET /v2/<name>/manifests/<reference>
        image_manifest = None
        repo_uri =  "{}/v2/{}/manifests/{}".format(docker_address, docker_repo, repo_tag)
        try:
            req = urllib.request.Request(repo_uri, method='GET')
            req.add_header('Authorization', auth_header)
            req.add_header('Accept', content_type)
            payload = urllib.request.urlopen(req).read()
            image_manifest = payload.decode('ascii')
            print(image_manifest)
            manifest_json = json.loads(image_manifest)
            from os.path import expanduser
            home_dir = expanduser("~")
            my_manifest_file = os.path.normpath(home_dir + "/horton/my_image_manifest.json")
            with open(my_manifest_file, 'w') as f:
                f.write(image_manifest)
            print(manifest_json)
        except Exception:
            print(Fore.RED + "Exception getting Docker image: " + repo_tag, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)

        for blob in manifest_json["fsLayers"]:
            blob_sum = blob["blobSum"]
            #content_type = blob["mediaType"]
            print(blob_sum)

            #GET /v2/<name>/blobs/<digest>
            repo_uri =  "{}/v2/{}/blobs/{}".format(docker_address, docker_repo, blob_sum)

            try:
                blob_chunk = None
                req = urllib.request.Request(repo_uri, method='GET')
                req.add_header('Authorization', auth_header)
                #req.add_header('Accept', content_type)
                ret = urllib.request.urlopen(req)
                blob_chunk = ret.read()
                #blob_chunk = content.decode('ascii')
                image_blob += blob_chunk
            except Exception:
                print(Fore.RED + "Exception getting Docker image: " + docker_repo, file=sys.stderr)
                traceback.print_exc()
                print(Fore.RESET, file=sys.stderr)
        return image_blob

    def build_auth_header2(self, username, password):
        puid = username + ':' + password
        puid_bytes = puid.encode('ascii')
        encoded_credentials = base64.b64encode(puid_bytes)
        auth_header = "Basic " + encoded_credentials.decode('ascii')
        return auth_header    

    def create_hotron_devices_from_manifest(self, input_manifest_file, save_manifest_file):
        hub_connect_string = self.get_env_connect_string()
        base_hostname = "hortondeploytest"
        deployment_name = base_hostname + '-' + self.get_random_num_string(10000)
        deployment_json = self.get_deployment_model_json(input_manifest_file)
        az_devices = []
        module_count = 0

        try:
            deployment_containers = deployment_json['containers']
            identity_json = deployment_json['identities']
            id_prefix = "horton_{}_{}".format(self.get_random_num_string(1000),self.get_random_num_string(1000))
            for azure_device in identity_json:
                az_device_id = identity_json[azure_device]
                objectType = self.get_json_value(az_device_id, 'objectType')
                objectName = self.get_json_value(az_device_id, 'objectName')
                if objectType == "iothub_device":
                    device_id = "{}_{}".format(id_prefix, objectName)
                    dev_object = self.populate_device_object(az_device_id, objectName, device_id)
                    dev_object.connectionString = self.create_iot_device(hub_connect_string, device_id)
                    dev_object.deviceId = device_id
                    child_modules = []
                    if(self.node_has_children(identity_json, azure_device, 'modules')):
                        modules = identity_json[azure_device]['modules']
                        for module in modules:
                            module_obj = self.populate_device_object(modules[module], module, device_id)
                            module_obj.deviceId = device_id
                            module_obj.moduleId = module
                            module_obj.connectionString = self.create_device_module(hub_connect_string, device_id, module)
                            child_modules.append(module_obj)
                            module_count += 1

                    if(len(child_modules) > 0):
                        dev_object.modules = child_modules
                    az_devices.append(dev_object)

                elif(objectType in ["iothub_service", "iothub_registry"]):
                    #dev_object = DeviceObject(objectName)
                    dev_object = self.populate_device_object(az_device_id, objectName, '')
                    dev_object.connectionString = hub_connect_string
                    az_devices.append(dev_object)

        except Exception as e:
            print(Fore.RED + "Exception Processing HortonManifest: " + input_manifest_file, file=sys.stderr)
            print(str(e) + Fore.RESET, file=sys.stderr)
            return

        print(Fore.GREEN + "Created {} Devices and {} Modules".format(len(az_devices), module_count) + Fore.RESET)

        # add device id's and connection strings back to horton_manifest & save it
        deployment_obj = DeploymentObject(deployment_name, az_devices, deployment_containers)
        new_manifest_json = json.dumps(deployment_obj, default = lambda x: x.__dict__, sort_keys=False, indent=2)
        try:
            with open(save_manifest_file, 'w') as f:
                f.write(new_manifest_json)
        except:
            print(Fore.RED + "ERROR: writing JSON manifest to: " + save_manifest_file + Fore.RESET, file=sys.stderr)

        print("create_hotron_devices_from_manifest Complete")
        return True

    def build_auth_header(self, username, password):
        puid = username + ':' + password
        puid_bytes = puid.encode('ascii')
        encoded_credentials = base64.b64encode(puid_bytes)
        auth_header = "Basic " + encoded_credentials.decode('ascii')
        return auth_header    

    def populate_device_object(self, device_json, object_name, deviceId=''):
        device_object = DeviceObject(object_name)
        if deviceId:
            device_object.deviceId     = deviceId
        else:
            device_object.deviceId      = self.get_json_value(device_json, 'deviceId')
        device_object.objectName        = self.get_json_value(device_json, 'objectName')
        device_object.objectType        = self.get_json_value(device_json, 'objectType')
        device_object.apiSurface        = self.get_json_value(device_json, 'apiSurface')
        device_object.adapterName       = self.get_json_value(device_json, 'adapterName')
        device_object.tcpPort           = self.get_json_value(device_json, 'tcpPort')
        device_object.connectionString  = self.get_json_value(device_json, 'connectionString')
        return device_object

    def node_has_children(self, json, node, name):
        try:
            children = json[node]
            if(children):
                if(children[name]):
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False

    def get_json_value(self, node, name):
        value = ""
        try:
            value = node[name]
        except:
            print(Fore.YELLOW + "ERROR: [{}] not found in JSON: ({})".format(name, node) + Fore.RESET, file=sys.stderr)
        return value
        
    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print(Fore.RED + "IOTHUB_E2E_CONNECTION_STRING not set in environment" + Fore.RESET, file=sys.stderr)
            sys.exit(1)
        return service_connection_string

    def create_iot_device(self, connect_string, device_name):
        dev_connect = ""
        try:
            helper = Helper(connect_string)
            helper.create_device(device_name)
            print("create_iot_device: ({}) returned: ({})".format(device_name, 'OK'))
            dev_connect = helper.get_device_connection_string(device_name)
        except Exception as e:
             print(Fore.RED + "Exception creating device: " + device_name, file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)

        return dev_connect
       
    def create_device_module(self, connect_string, device_name, module_name):
        mod_connect = None
        try:
            helper = Helper(connect_string)
            helper.create_device_module(device_name, module_name)
            print("create_device_module: ({}/{}) returned: ({})".format(device_name, module_name, 'OK'))
            mod_connect = helper.get_module_connection_string(device_name, module_name)
        except Exception as e:
             print(Fore.RED + "Exception creating device: {}/{}".format(device_name, module_name), file=sys.stderr)
             traceback.print_exc()
             print(Fore.RESET, file=sys.stderr)
        return mod_connect

    def create_device_connectstring2(self, hub_connectstring, device_name, access_key):
        connect_parts = hub_connectstring.split(';')
        device_connectstring = "{};DeviceId={};SharedAccessKey={}".format(connect_parts[0], device_name, access_key)
        return device_connectstring

    def create_module_connectstring2(self, hub_connectstring, device_name, module_name, access_key):
        connect_parts = hub_connectstring.split(';')
        device_connectstring = "{};DeviceId={};ModuleId={};SharedAccessKey={}".format(connect_parts[0], device_name, module_name, access_key)
        return device_connectstring

    def get_random_num_string(self, maxval):
        from random import randrange
        randnum = randrange(maxval)
        return str(randnum).zfill(len(str(maxval)))        

    def get_deployment_model_json(self, json_filename):
        json_manifest = ''
        try:
            with open(json_filename, 'r') as f:
                json_manifest = json.loads(f.read())
        except Exception as e:
            print(Fore.RED + "ERROR: in JSON manifest: " + json_filename + Fore.RESET, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)
        return json_manifest

class DeviceObject:
    def __init__ (self, objectName, objectType='', apiSurface='', adapterName='', tcpPort='', deviceId='', connectionString=''):
        self.objectName       = objectName
        self.objectType       = objectType
        self.apiSurface       = apiSurface
        self.adapterName      = adapterName
        self.tcpPort          = tcpPort
        self.deviceId         = deviceId
        self.connectionString = connectionString

class DeploymentObject:  
    def __init__ (self, deployment_name, identities=None, deployment_containers=None):
        self.deployment_name  = deployment_name
        self.containers       = deployment_containers
        self.identities = identities

if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])
