#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: deploy_horton.py
# author:   v-greach@microsoft.com
# created:  03/15/2019
# Rev: 03/19/2019 H

import sys
import os
import json
import shutil
import traceback
import base64
from colorama import init, Fore, Back, Style
import iothub_service_client
from iothub_service_client import IoTHubRegistryManager, IoTHubRegistryManagerAuthMethod
from iothub_service_client import IoTHubDeviceStatus, IoTHubError

class DeployHorton:

    def __init__(self, args):

        az_devices = []
        module_count = 0
        init(convert=True)

        input_manifest_file = "/IoT_TestData/Horton/horton_maifest_template_001.json"
        save_manifest_file = "/iot_testdata/horton/horton_updated_manifest.json"
        hub_connect_string = self.get_env_connect_string()
        base_hostname = "hortondeploytest"
        deployment_name = base_hostname + '-' + self.get_random_num_string(10000)
        deployment_json = self.get_deployment_model_json(input_manifest_file)

        try:
            azure_ids = deployment_json['azure_identities']
            for azure_device in azure_ids:
                device_connectstring = ''
                children_modules = []
                az_device_name = self.get_json_value(azure_device, 'device_name')
                # TEST_TEST_TEST  - NextLines:1
                az_device_name      = 'D0_' + az_device_name + "_" + self.get_random_num_string(100)
                az_device_type      = self.get_json_value(azure_device, 'device_type')
                az_device_id_suffix = self.get_json_value(azure_device, 'device_id_suffix')
                az_docker_image     = self.get_json_value(azure_device, 'docker_image')
                az_docker_container = self.get_json_value(azure_device, 'docker_container')
                az_docker_args      = self.get_json_value(azure_device, 'docker_args')
                
                if(self.node_has_children(azure_device)):
                    children = azure_device['children']
                    for child in children:
                        child_module_id        = self.get_json_value(child, 'module_id')
                        child_module_type      = self.get_json_value(child, 'module_type')
                        child_docker_image     = self.get_json_value(child, 'module_docker_image_name')
                        child_docker_container = self.get_json_value(child, 'module_docker_container_name')
                        child_docker_args      = self.get_json_value(child, 'module_docker_creation_args')
                        new_module = DeviceModuleObject(child_module_id, az_device_name, child_module_type, child_docker_image, child_docker_container, child_docker_args, '')
                        children_modules.append(new_module)

                if(az_device_type == 'iothub_device'):
                    new_device = self.create_iot_device(hub_connect_string, az_device_name + az_device_id_suffix)
                    if(new_device):
                        device_connectstring = self.create_device_connectstring(hub_connect_string, az_device_name + az_device_id_suffix, new_device.primaryKey)
                else:
                    new_device = None

                child_module_objects = []
                for child_module in children_modules:
                    if(child_module.module_type == 'iothub_module'):
                        new_module = self.create_device_module(hub_connect_string, az_device_name + az_device_id_suffix, child_module.module_id)
                        if(new_module):
                            child_module.module_connect_string = self.create_module_connectstring(hub_connect_string, az_device_name + az_device_id_suffix, child_module.module_id, new_module.primaryKey)
                            child_module_objects.append(child_module)
                            module_count += 1

                new_device_obj = IotDeviceObject(az_device_name, az_device_type, az_device_id_suffix, device_connectstring, az_docker_image, az_docker_container, az_docker_args)
                new_device_obj.children = children_modules
                az_devices.append(new_device_obj)

        except Exception as e:
            print(Fore.RED + "Exception Processing HortonManifest: " + input_manifest_file, file=sys.stderr)
            print(str(e) + Fore.RESET, file=sys.stderr)
            return

        print(Fore.GREEN + "Created {} Devices and {} Modules".format(len(az_devices), module_count) + Fore.RESET)

        # add device id's and connection strings back to horton_manifest & save it
        deployment_obj = DeploymentObject(deployment_name, az_devices)
        new_manifest_json = json.dumps(deployment_obj, default = lambda x: x.__dict__, sort_keys=False, indent=2)
        try:
            with open(save_manifest_file, 'w') as f:
                f.write(new_manifest_json)
        except:
            print(Fore.RED + "ERROR: writing JSON manifest to: " + save_manifest_file + Fore.RESET, file=sys.stderr)

        print("PHASE1 Complete")

        self.setup_docker_containers(hub_connect_string, deployment_obj)

        print("DONE")

    def setup_docker_containers(self, hub_connect_string, deployment_obj):
        from os.path import dirname, join, abspath
        sys.path.insert(0, abspath(join(dirname(__file__), '../horton_helpers')))
        from containers import all_containers
        import urllib
        import base64
        import docker

        if not ("IOTHUB_E2E_REPO_ADDRESS" in os.environ
            and "IOTHUB_E2E_CONNECTION_STRING" in os.environ
            and "IOTHUB_E2E_REPO_USER" in os.environ
            and "IOTHUB_E2E_REPO_PASSWORD" in os.environ):
            print("Error: Docker container repository credentials are not set in IOTHUB_E2E_REPO* environment variables.")
            return

        #e2e_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        repo_address = "https://" + os.environ["IOTHUB_E2E_REPO_ADDRESS"]
        repo_user = os.environ["IOTHUB_E2E_REPO_USER"]
        repo_password = os.environ["IOTHUB_E2E_REPO_PASSWORD"]

        repository = 'bertk-csharp-lkg'
        repo_tag = 'latest'

        #docker_client = docker.DockerClient.login(repo_user, repo_password, '', repo_address)
        #docker.APIClient.login('username', '*******', 'email@gmail.com','https://index.docker.io/v1/', config)        docker_client = docker.DockerClient.login() .login(repo_user, repo_password, '', repo_address)
        #config = os.path.join('/', 'IGui') + 'config.json'
        #try:
        #    docker_client = docker.APIClient.login(repo_user, repo_password, 'email@gmail.com', repo_address, config)
        #    docker_containers = docker_client.containers.list(all=True)
        #except Exception as e:
        #    print(Fore.RED + "Exception connecting to Docker: " + repo_address, file=sys.stderr)
        #    traceback.print_exc()
        #    print(e + Fore.RESET, file=sys.stderr)

        #"$Registry/v2/$Repository/manifests/$TAG_OLD"
        uri =  "{}/v2/{}/manifests/{}".format(repo_address, repository, repo_tag)

        content_type = 'application/vnd.docker.distribution.manifest.v2+json'
        auth_header = self.build_auth_header(repo_user, repo_password)

        #req = urllib.request.Request(repo_address, method='GET')
        try:
            req = urllib.request.Request(uri, method='GET')
            req.add_header('Authorization', auth_header)
            req.add_header('Accept', content_type)
            #resp = urllib.request.urlopen(req)
            content = urllib.request.urlopen(req).read()
            #charset = resp.info().get_content_charset()
            #content = resp.read()
            #content = resp.read().decode(charset)
            #req=urllib.request.urlopen(URL)
            #charset=req.info().get_content_charset()
            #content=req.read().decode(charset)            
            #x = content.ByteArray()
            #$Manifest = ConvertFrom-ByteArray -Data $Response.Content -Encoding ASCII
            #print(content)
            #manifest = [x.decode('utf-8') for x in content]
            #manifest = bytes(content, 'ascii')
            #manifest = ''.join(bytelist).decode('utf-8')
            #manifest = ''.join(content.decode()).decode('ascii')
            #manifest = ''.join(content.decode()).decode('ascii')
            manifest = content.decode('ascii')
            print(manifest)

            data = json.loads(manifest)
            print(data)

            save_file = "/iot_testdata/horton/docker_repo.json"
            docker_json = json.dumps(data, default = lambda x: x.__dict__, sort_keys=False, indent=2)
            try:
                with open(save_file, 'w') as f:
                    f.write(docker_json)
            except:
                print(Fore.RED + "ERROR: writing JSON docker to: " + save_file + Fore.RESET, file=sys.stderr)

        except Exception as e:
             print(Fore.RED + "Exception connecting to Docker: " + repo_address, file=sys.stderr)
             traceback.print_exc()
             print(e + Fore.RESET, file=sys.stderr)


        #req = urllib.request.Request(repo_address, data=b'DATA!', method='PUT')
        #urllib.request.urlopen(req)

        #for cntr in docker_containers:
        #    print(cntr)

        for cntr in all_containers:
            print(cntr)

        deployment_devices = deployment_obj.azure_identities
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        try:
            iothub_registry_manager = IoTHubRegistryManager(hub_connect_string)
        except Exception as e:
            print(Fore.RED + "Exception connecting to IoT Hub: " + hub_connect_string + Fore.RESET, file=sys.stderr)

        api_client = docker.APIClient(base_url="unix://var/run/docker.sock")

        print("Deployment: " + deployment_obj.deployment_name)
        for device in deployment_devices:
            print("....DeviceName: " + device.device_name)
            if(device.docker_container):
                container = device.docker_container
                if(container in all_containers):
                    docker_containers = api_client.containers(all=True)
                    for docker_container in docker_containers:
                        print(docker_container)

            for module in device.children:
                print("........Module: " + module.module_id)

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

        return

    def build_auth_header(self, username, password):
        #pair = "{}:{}".format(username, password)
        puid = username + ':' + password
        puid_bytes = puid.encode('ascii')
        #puid_bytes = puid_ascii.encode('utf-8')
        #encoded_credentials = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($Pair))
        encoded_credentials = base64.b64encode(puid_bytes)
        #Params.Headers.Add('Authorization', "Basic $encodedCredentials")
        base64string = base64.b64decode(encoded_credentials).decode('utf-8')
        base64string = 'aW90c2RrZTJlOkgwMzRCUkxVVHRORkhnOFN3MGppaVg4S204PXVDSGtu'
        auth_header = "Basic {}".format(base64string)
        #auth_header = "Basic " + encoded_credentials
        auth_header = "Basic " + encoded_credentials.decode('ascii')
        return auth_header    

    def node_has_children(self, node):
        try:
            children = node['children']
            if(children):
                return True
            else:
                return False
        except:
            return False

    def get_json_value(self, node, name):
        value = ""
        try:
            value = node[name]
        except:
            print(Fore.YELLOW + "ERROR: value not found in JSON: ({}/{})".format(node, name) + Fore.RESET, file=sys.stderr)
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
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        new_device = None
        try:
            iothub_registry_manager = IoTHubRegistryManager(connect_string)
            new_device = iothub_registry_manager.create_device(device_name, "", "", auth_method)
        except Exception as e:
            print(Fore.RED + "Exception Creating device: " + device_name, file=sys.stderr)
            print(str(e) + Fore.RESET, file=sys.stderr)
        return new_device

    def create_device_module(self, connect_string, device_id, module_name):
        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY
        new_module = None
        try:
            iothub_registry_manager = IoTHubRegistryManager(connect_string)
            new_module = iothub_registry_manager.create_module(device_id, '', '', module_name, auth_method)
        except Exception as e:
            print(Fore.RED + "Exception Creating device/module: " + module_name, file=sys.stderr)
            print(str(e) + Fore.RESET, file=sys.stderr)
        return new_module

    def create_device_connectstring(self, hub_connectstring, device_name, access_key):
        connect_parts = hub_connectstring.split(';')
        device_connectstring = "{};DeviceId={};SharedAccessKey={}".format(connect_parts[0], device_name, access_key)
        return device_connectstring

    def create_module_connectstring(self, hub_connectstring, device_name, module_name, access_key):
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
        except:
            print(Fore.RED + "ERROR: in JSON manifest: " + json_filename + Fore.RESET, file=sys.stderr)
        return json_manifest

class DeviceModuleObject:  
    def __init__ (self, module_id, device_name='', module_type='', module_docker_image_name='', module_docker_container_name='', module_docker_creation_args='', module_connect_string=''):
        self.module_id                    = module_id
        self.device_name                  = device_name
        self.module_type                  = module_type
        self.module_docker_image_name     = module_docker_image_name
        self.module_docker_container_name = module_docker_container_name
        self.module_docker_creation_args  = module_docker_creation_args
        self.module_connect_string        = module_connect_string

class IotDeviceObject:  
    def __init__ (self, device_name='', device_type='', device_id_suffix='', device_connect_string='', docker_image='', docker_container='', docker_args='', children=None):
        self.device_name             = device_name
        self.device_type             = device_type
        self.device_id_suffix        = device_id_suffix
        self.device_connect_string   = device_connect_string
        self.docker_image            = docker_image
        self.docker_container        = docker_container
        self.docker_args             = docker_args
        self.children                = children

class DeploymentObject:  
    def __init__ (self, deployment_name, azure_identities=None):
        self.deployment_name  = deployment_name
        self.azure_identities = azure_identities

class AzureIdObject:  
    def __init__ (self, azure_devices=None, ks=[], vs=[]):
        self.azure_identities = azure_devices
        self.__dict__ = dict(zip(ks, vs))

class DeviceChildrenObject:  
    def __init__ (self, ks=[], vs=[]):
        self.__dict__ = dict(zip(ks, vs))

if __name__ == "__main__":
    horton_deploymnet = DeployHorton(sys.argv[1:])