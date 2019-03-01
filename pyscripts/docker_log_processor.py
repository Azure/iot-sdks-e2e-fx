#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# update-edge-config.py
# v-greach@microsoft.com

import os
import shutil
import pathlib

# Test Settings
config_directory="/git/iot/iot-sdk-testapps/UpdateEdgeConfig"
config_filename="config.yaml"
config_save="config.save.yaml"
config_working="config.working.yaml"
os.chdir(config_directory)

original_file = os.path.join(os.sep, config_directory, config_filename)
save_file = os.path.join(os.sep, config_directory, config_save)
working_file = os.path.join(os.sep, config_directory, config_working)

shutil.copy(original_file, save_file)
shutil.copy(original_file, working_file)

import sys
import argparse
from ruamel.yaml import YAML

def get_hostname(workingfile):
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

def enable_debug(workingfile):
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

def disable_debug(workingfile):
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

def get_connection_string(workingfile):
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

def set_connection_string(workingfile, connection):
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

def enable_unix_sockets(workingfile):
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

def enable_http_sockets(workingfile):
    yaml = YAML()
    try:
        with open(workingfile) as input_file:
            config_yaml = yaml.load(input_file)
            config_yaml["connect"]["management_uri"] = "http://127.0.0.1:15581"
            config_yaml["connect"]["workload_uri"] = "http://127.0.0.1:15580"
            config_yaml["listen"]["management_uri"] = "http://0.0.0.0:15581"
            config_yaml["listen"]["workload_uri"] = "http://0.0.0.0:15580"
        with open(workingfile, "w") as file:
            yaml.dump(config_yaml, file)
    except Exception as e:
        print("Exception processing YAML: " + workingfile)
        print(e)
        return False
    return True

def is_list_of_strings(lst):
    return bool(lst) and isinstance(lst, list) and all(isinstance(elem, str) for elem in lst)

# Proccess command line args
cmdline = []

if len(sys.argv) > 1:
    cmdline = sys.argv
else:
    # for TESTING
    #cmdline = "-enable-http-sockets "
    #cmdline += "-disable-debug "
    #cmdline += "-get-connection-string "
    #cmdline = "-get-hostname"
    #cmdline += "-set-connection-string fooconn"
    cmdline += "-enable-http-sockets"

if len(cmdline) > 1:
    parser = argparse.ArgumentParser(description="Iot Edge Config Update")
    parser.add_argument('-enable-http-sockets', default=False, action='store_true', help="enables http sockets")
    parser.add_argument('-enable-unix-sockets', default=False, action='store_true', help="enables unix sockets")
    parser.add_argument('-enable-debug', default=False, action='store_true', help="turns on debugging")
    parser.add_argument('-disable-debug', default=False, action='store_true', help="turns off debugging")
    parser.add_argument('-get-hostname', action='store_true', help="returns hostname")
    parser.add_argument('-get-connection-string', default=False, action='store_true', help="returns connection string")
    parser.add_argument('-set-connection-string', nargs=1, help="sets connection string")

    cmdsplit = []
    if is_list_of_strings(cmdline):
        tmpstr = ""
        tmpstr += tmpstr.join(cmdline)
        if ' ' in tmpstr:
            cmdsplit = tmpstr.split(' ')
        else:
            cmdsplit.append(tmpstr)
    else:
        cmdsplit = cmdline.split(' ')

    arguments = parser.parse_args(cmdsplit)
   
    if(arguments.get_hostname):
        host = get_hostname(working_file)
        print(host)
    if(arguments.enable_debug):
        if(enable_debug(working_file)):
            shutil.copy(working_file, original_file)
            print("Debug Enabled")
    if(arguments.disable_debug):
        if(disable_debug(working_file)):
            shutil.copy(working_file, original_file)
            print("Debug Disabled")
    if(arguments.get_connection_string):
        connection = get_connection_string(working_file)
        print("connection OUT: " + connection)
    if(arguments.set_connection_string):
        connection = getattr(arguments, 'set_connection_string')
        if(set_connection_string(working_file, connection[0])):
            shutil.copy(working_file, original_file)
            print("Connection string set to :" + connection[0])
    if(arguments.enable_unix_sockets):
        if(enable_unix_sockets(working_file)):
            shutil.copy(working_file, original_file)
            print("Unix sockets enabled")
    if(arguments.enable_http_sockets):
        if(enable_http_sockets(working_file)):
            shutil.copy(working_file, original_file)
            print("HTTP sockets enabled")
else:
    print("Invalid command line")
    