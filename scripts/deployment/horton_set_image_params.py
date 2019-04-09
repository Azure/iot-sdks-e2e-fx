#!/usr/bin/env python
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

    def __init__(self, manifest_name, object_name, image_path='', image_tag='', create_options=''):
        self.horton_image_params(manifest_name, object_name, image_path, image_tag, create_options)

    def horton_image_params(self, manifest_name, object_name, image_path='', image_tag='', create_options=''):
        init(autoreset=True)
        manifest_json = self.get_deployment_model_json(manifest_name)
        object_json = manifest_json['containers'][object_name]

        if image_path:
            try:
                object_json['image'] = image_path
                manifest_json['containers'][object_name] = object_json
            except:
                print(Fore.RED + "ERROR: in JSON create_options: " + image_path, file=sys.stderr)
                traceback.print_exc()
                sys.exit(-1)
        if image_tag:
            try:
                object_json['imageTag'] = image_tag
                manifest_json['containers'][object_name] = object_json
            except:
                print(Fore.RED + "ERROR: in JSON create_options: " + image_tag, file=sys.stderr)
                traceback.print_exc()
                sys.exit(-1)
                return
        if create_options:
            try:
                create_opt_json = json.loads(create_options)
                object_json['createOptions'] = create_opt_json
                manifest_json['containers'][object_name] = object_json
            except:
                print(Fore.RED + "ERROR: in JSON create_options: " + create_options, file=sys.stderr)
                traceback.print_exc()
                sys.exit(-1)
                return

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
    parser.add_argument('--image_path', default='', help='imagePath in manifest to update', type=str)
    parser.add_argument('--image_tag', default='', help='imageTag in manifest to update', type=str)
    parser.add_argument('--create_options', default='', help='createOptions in manifest to update (dict)', type=str)
    arguments = parser.parse_args()
    image_params = HortonSetImageParams(arguments.manifest, arguments.object_name, arguments.image_path, arguments.image_tag, arguments.create_options)
