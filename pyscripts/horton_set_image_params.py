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
from colorama import init, Fore, Back, Style

class HortonSetImageParams:

    #deployment_template.json serviceObject '"HostConfig": {"PortBindings": {"8080/tcp": [{"HostPort": "8071"}],"22/tcp": [{"HostPort": "8171"}]},"CapAdd": "SYS_PTRACE"}'
    def __init__(self, manifest_name, object_name, image_path, create_options=''):
        init(convert=True)

        manifest_json = self.get_deployment_model_json(manifest_name)
        object_json = manifest_json['containers'][object_name]
        object_json['image'] = image_path

        if create_options:
            object_json['createOptions'] = create_options

        manifest_json['containers'][object_name] = object_json
        with open(manifest_name + 'x', 'w') as f:
            f.write(json.dumps(manifest_json, default = lambda x: x.__dict__, sort_keys=False, indent=2))

    def get_deployment_model_json(self, json_filename):
        json_manifest = ''
        try:
            with open(json_filename, 'r') as f:
                json_manifest = json.loads(f.read())
        except:
            print(Fore.RED + "ERROR: in JSON manifest: " + json_filename + Fore.RESET, file=sys.stderr)
            traceback.print_exc()
            print(Fore.RESET, file=sys.stderr)
        return json_manifest
