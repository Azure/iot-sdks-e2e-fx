# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_set_image_params.py
# author:   v-greach@microsoft.com 

import sys
import os
import json
import traceback
import argparse
from colorama import init, Fore, Back, Style

class HortonSetImageParams:

    def __init__(self, manifest_name, object_name, module_name='', image_path='', image_tag='', 
        tcp_port=0, container_port=0, create_options=''):
            self.horton_image_params(manifest_name, object_name, module_name, image_path, image_tag, 
            tcp_port, container_port, create_options)

    def horton_image_params(self, manifest_name, object_name, module_name='', image_path='', image_tag='', 
            tcp_port=0, container_port=0, create_options=''):

        init(autoreset=True)
        manifest_json = self.get_deployment_model_json(manifest_name)
        object_json = self.get_json_object(manifest_json, object_name, module_name)

        try:
            if image_path:
                object_json['image'] = image_path
                self.save_json_object(manifest_name, manifest_json, object_json, object_name, module_name)
            if image_tag:
                object_json['imageTag'] = image_tag
                self.save_json_object(manifest_name, manifest_json, object_json, object_name, module_name)
            if tcp_port:
                object_json['tcpPort'] = str(tcp_port)
                self.save_json_object(manifest_name, manifest_json, object_json, object_name, module_name)
            if container_port:
                object_json['containerPort'] = str(container_port)
                self.save_json_object(manifest_name, manifest_json, object_json, object_name, module_name)
            if create_options:
                create_opt_json = json.loads(create_options)
                object_json['createOptions'] = create_opt_json
                self.save_json_object(manifest_name, manifest_json, object_json, object_name, module_name)
        except:
            print(Fore.RED + "ERROR: in JSON create_options: " + create_options, file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)

    def get_json_object(self, manifest_json, object_name, module_name=''):
        try:
            if module_name:
                return manifest_json['identities'][object_name]['modules'][module_name]
            else:
                if object_name in manifest_json['identities']:
                    return manifest_json['identities'][object_name]
                if object_name in manifest_json['containers']:
                    return manifest_json['containers'][object_name]
        except:
            print(Fore.RED + "ERROR: could not find ({}:{}) in JSON containers/identities/modules: ".format(object_name, module_name), file=sys.stderr)
            traceback.print_exc()
            sys.exit(-1)

    def save_json_object(self, manifest_name, manifest_json, object_json, object_name, module_name=''):

        if module_name:
            if module_name in manifest_json['identities'][object_name]['modules'][module_name]:
                manifest_json['identities'][object_name]['modules'][module_name] = object_json
        else:
            if object_name in manifest_json['identities']:
                manifest_json['identities'][object_name] = object_json
            if object_name in manifest_json['containers']:
                manifest_json['containers'][object_name] = object_json

        with open(manifest_name, 'w') as f:
            f.write(json.dumps(manifest_json, default = lambda x: x.__dict__, sort_keys=False, indent=2))

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update ImageParams Horton Manifest')
    parser.add_argument('--manifest', required=True, help='path and filename of manifest', type=str)
    parser.add_argument('--object_name', required=True, help='objectName in manifest', type=str)
    parser.add_argument('--module_name', default='', help='moduleName in manifest to update', type=str)
    parser.add_argument('--image_tag', default='', help='imageTag in manifest to update', type=str)
    parser.add_argument('--tcp_port', default=0, help='tcpPort in manifest to update', type=int)
    parser.add_argument('--container_port', default=0, help='containerPort in manifest to update', type=int)
    parser.add_argument('--create_options', default='', help='createOptions in manifest to update (dict)', type=str)
    arguments = parser.parse_args()
    image_params = HortonSetImageParams(arguments.manifest, arguments.object_name, arguments.module_name, arguments.image_path, 
                   arguments.image_tag, arguments.tcp_port, arguments.container_port, arguments.create_options)
