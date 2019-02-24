#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from service_helper import Helper
from identity_helpers import get_random_device_name
from edge_configuration import EdgeConfiguration
from containers import all_containers
import random
import string
import os


def createNewHubInstance(service_connection_string):
    """
    Create a new edgeHub device using the connection string that is passed in.  Returns an EdgeHub object that can be used to configure the edgeHub instance.
    """
    return EdgeHub(service_connection_string)


def useExistingHubInstance(service_connection_string, edge_hub_device_id):
    """
    Returns an EdgeHub object that can be used to configure the edgeHub instance using the passed parameters
    """
    return EdgeHub(service_connection_string, edge_hub_device_id)


class EdgeHub:
    def __init__(self, service_connection_string, edge_hub_device_id=None):
        self.service_connection_string = service_connection_string
        self.helper = Helper(self.service_connection_string)
        if not edge_hub_device_id:
            self._createNewHub()
        else:
            self._useExistingHub(edge_hub_device_id)

    def _createNewHub(self):
        self.edge_hub_device_id = get_random_device_name()
        self.helper.create_device(self.edge_hub_device_id, True)
        self._finishHubSetup()

    def _useExistingHub(self, edge_hub_device_id):
        self.edge_hub_device_id = edge_hub_device_id
        self._finishHubSetup()

    def _finishHubSetup(self):
        self.edge_hub_connection_string = self.helper.get_device_connection_string(
            self.edge_hub_device_id
        )

        self.leaf_device_id = self.edge_hub_device_id + "_leaf_device"
        try:
            self.leaf_device_connection_string = self.helper.get_device_connection_string(
                self.leaf_device_id
            )
        except:
            self.helper.create_device(self.leaf_device_id)
            self.leaf_device_connection_string = self.helper.get_device_connection_string(
                self.leaf_device_id
            )

        self._discoverAllExistingModules()

    def _discoverAllExistingModules(self):
        self.modules = []
        for name in all_containers:
            mod = all_containers[name]
            try:
                thisModString = self.helper.get_module_connection_string(
                    self.edge_hub_device_id, mod.module_id
                )
            except:
                pass
            else:
                mod.connection_string = thisModString
                self.modules.append(mod)

    def deployModules(self, modules):
        configuration = EdgeConfiguration()
        configuration.add_module(all_containers["friend"])

        for name in modules.split(","):
            name = name.strip()
            if name in all_containers:
                configuration.add_module(all_containers[name])
            else:
                print("module {} is invalid".format(name))
                print("valid modules are {0}".format(", ".join(all_containers.keys())))
                raise Exception("module " + name + " not defined")

        self.helper.apply_configuration(
            self.edge_hub_device_id, configuration.get_module_config()
        )
