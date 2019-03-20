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
import iothub_service_client
from iothub_service_client import IoTHubRegistryManager, IoTHubRegistryManagerAuthMethod
from iothub_service_client import IoTHubDeviceStatus, IoTHubError
#from iothub_service_client_args import get_iothub_opt, OptionError

class HortonTools:

    def __init__(self, args):

        #init(convert=True)

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
        #print(Fore.RED + "######################################")
        #print(conn_string)
        #code = input("Enter the secret code to NUKE ALL DEVICES: ")
        #if(code == 'WtF'):

        print('NUKING ' + conn_string)

        auth_method = IoTHubRegistryManagerAuthMethod.SHARED_PRIVATE_KEY

        iothub_registry_manager = IoTHubRegistryManager(conn_string)

        number_of_devices = 10

        dev_list = iothub_registry_manager.get_device_list(number_of_devices)
        devices_got = len(dev_list)
        total = devices_got
        dev_count = 0

        while(devices_got != 0):
            print ( "Number of devices : {0}".format(devices_got) )

            for device in range(0, devices_got):
                dev_count += 1
                iothub_device = dev_list[device]
                print ( "DELETING:{} ------ {}".format(dev_count, iothub_device.deviceId))
                device_id = iothub_device.deviceId
                iothub_registry_manager.delete_device(device_id)

            dev_list = iothub_registry_manager.get_device_list(number_of_devices)
            devices_got = len(dev_list)
            total += devices_got

        print("TOTAL DELETED: {}".format(total))

        return

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





if __name__ == "__main__":
    horton_tools = HortonTools(sys.argv[1:])
