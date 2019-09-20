# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# update-edge-config.py
# author:   v-greach@microsoft.com
# created:  02/11/2019
# Rev: 03/11/2019 B

import os
import shutil
import sys
import argparse
from ruamel.yaml import YAML
import pathlib

class UpdateEdgeConfig:

    def __init__(self, args):

        original_file = "/etc/iotedge/config.yaml"
        working_file = "/etc/iotedge/config.working.yaml"
        shutil.copy(original_file, working_file)

        parser = argparse.ArgumentParser(description="Iot Edge Config Update")
        parser.add_argument('-enable-http-sockets', default=False, action='store_true', help="enables http sockets")
        parser.add_argument('-enable-unix-sockets', default=False, action='store_true', help="enables unix sockets")
        parser.add_argument('-enable-debug', default=False, action='store_true', help="turns on debugging")
        parser.add_argument('-disable-debug', default=False, action='store_true', help="turns off debugging")
        parser.add_argument('-get-hostname', action='store_true', help="returns hostname")
        parser.add_argument('-get-connection-string', default=False, action='store_true', help="returns connection string")
        parser.add_argument('-set-connection-string', nargs=1, help="sets connection string")
        arguments = parser.parse_args(args)
    
        if(arguments.get_hostname):
            host = self.get_hostname(working_file)
            print(host)
        elif(arguments.enable_debug):
            if(self.enable_debug(working_file)):
                shutil.copy(working_file, original_file)
                print("Debug Enabled")
        elif(arguments.disable_debug):
            if(self.disable_debug(working_file)):
                shutil.copy(working_file, original_file)
                print("Debug Disabled")
        elif(arguments.get_connection_string):
            connection = self.get_connection_string(working_file)
            print(connection)
        elif(arguments.set_connection_string):
            connection = getattr(arguments, 'set_connection_string')
            if(self.set_connection_string(working_file, connection[0])):
                shutil.copy(working_file, original_file)
                print("Connection string set to :" + connection[0])
        elif(arguments.enable_unix_sockets):
            if(self.enable_unix_sockets(working_file)):
                shutil.copy(working_file, original_file)
                print("Unix sockets enabled")
        elif(arguments.enable_http_sockets):
            if(self.enable_http_sockets(working_file)):
                shutil.copy(working_file, original_file)
                print("HTTP sockets enabled")
 
    def get_hostname(self, workingfile):
        yaml = YAML()
        hostname = "hostname NOT FOUND"
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                hostname = config_yaml["hostname"]
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
        return hostname

    def enable_debug(self, workingfile):
        yaml = YAML()
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                config_yaml["agent"]["env"]["RuntimeLogLevel"] = "debug"
            with open(workingfile, "w") as file:
                yaml.dump(config_yaml, file)
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
            return False
        return True

    def disable_debug(self, workingfile):
        yaml = YAML()
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                if "RuntimeLogLevel" in config_yaml["agent"]["env"]:
                    del config_yaml["agent"]["env"]["RuntimeLogLevel"]
            with open(workingfile, "w") as file:
                yaml.dump(config_yaml, file)
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
            return False
        return True

    def get_connection_string(self, workingfile):
        yaml = YAML()
        connect = "connectstring NOT FOUND"
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                connect = config_yaml["provisioning"]["device_connection_string"]
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
        return connect

    def set_connection_string(self, workingfile, connection):
        yaml = YAML()
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                config_yaml["provisioning"]["device_connection_string"] = connection
            with open(workingfile, "w") as file:
                yaml.dump(config_yaml, file)
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
            return False
        return True

    def enable_unix_sockets(self, workingfile):
        yaml = YAML()
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                config_yaml["connect"]["management_uri"] = "unix:///var/run/iotedge/mgmt.sock"
                config_yaml["connect"]["workload_uri"] = "unix:///var/run/iotedge/workload.sock"
                config_yaml["listen"]["management_uri"] = "fd://iotedge.mgmt.socket"
                config_yaml["listen"]["workload_uri"] = "fd://iotedge.socket"
            with open(workingfile, "w") as file:
                yaml.dump(config_yaml, file)
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
            return False
        return True

    def enable_http_sockets(self, workingfile):
        yaml = YAML()
        local_ip = self.get_local_ip()
        try:
            with open(workingfile) as input_file:
                config_yaml = yaml.load(input_file)
                config_yaml["connect"]["management_uri"] = "http://" + local_ip + ":15581"
                config_yaml["connect"]["workload_uri"] = "http://" + local_ip + ":15580"
                config_yaml["listen"]["management_uri"] = "http://0.0.0.0:15581"
                config_yaml["listen"]["workload_uri"] = "http://0.0.0.0:15580"
            with open(workingfile, "w") as file:
                yaml.dump(config_yaml, file)
        except Exception as e:
            print("Exception processing YAML: " + workingfile)
            print(e)
            return False
        return True

    def get_local_ip(self):
        import netifaces
        ip_addresses = []
        for interface in netifaces.interfaces():
            interface_addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET not in interface_addresses:
                continue
            for address_data in interface_addresses[netifaces.AF_INET]:
                if address_data.get('addr') != '127.0.0.1':
                    ip_addresses.append(address_data.get('addr'))
        return ip_addresses[0]

if __name__ == "__main__":
    edge_processor = UpdateEdgeConfig(sys.argv[1:])
    
