#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import ruamel.yaml


class ConfigFile:
    def __init__(self):
        self.yaml = ruamel.yaml.YAML()  # defaults to round-trip if no parameters given
        self.yaml.preserve_quotes = True

        with open("/etc/iotedge/config.yaml", "r") as stream:
            self.contents = self.yaml.load(stream)

    def save(self):
        with open("/etc/iotedge/config.yaml", "w") as stream:
            self.yaml.dump(self.contents, stream)
