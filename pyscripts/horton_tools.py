#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: horton_tools.py
# author:   v-greach@microsoft.com
# created:  03/15/2019
# Rev: 03/18/2019 B

import sys
import os
import json
import shutil
from colorama import init, Fore, Back, Style
import iothub_service_client
from iothub_service_client import IoTHubRegistryManager, IoTHubRegistryManagerAuthMethod
from iothub_service_client import IoTHubDeviceStatus, IoTHubError

class HortonTools:

    def __init__(self, args):

        init(convert=True)

        az_devices = []
        connect_string = self.get_env_connect_string()

        #TEST_TEST_TEST
        self.NUKE_ALL_DEVICES_IN_HUB(connect_string)

    def get_env_connect_string(self):
        service_connection_string = ""
        try:  
            service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
        except KeyError: 
            print(Fore.RED + "IOTHUB_E2E_CONNECTION_STRING not set in environment", file=sys.stderr)
            print(Fore.RESET + " ", file=sys.stderr)
            sys.exit(1)
        return service_connection_string


    #####################
    ### INTERNAL ONLY ###
    #####################
    def NUKE_ALL_DEVICES_IN_HUB(self, conn_string):
        print(Fore.RED + "######################################")
        print(conn_string)
        code = input("Enter the secret code to NUKE ALL DEVICES: ")
        if(code == 'WtF'):
            print('NUKING ' + conn_string)

        return

if __name__ == "__main__":
    horton_tools = HortonTools(sys.argv[1:])
