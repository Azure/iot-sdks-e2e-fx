
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from connection_string import connection_string_to_dictionary
import os
import sys
import identity_helpers

format = ""


def usage():
    print("Usage get_environment_variables.py [format]")
    print('format can be one of "windows", "linux", "powershell", or "pycharm"')
    print("if not specified, format will be autodetected based on OS")
    sys.exit(1)


def print_env(env):
    global format
    if env in os.environ:
        if format == "linux":
            print('export {}="{}"'.format(env, os.environ[env]))
        elif format == "windows":
            print("set {}={}".format(env, os.environ[env]))
        elif format == "powershell":
            print("{}={}".format(env, os.environ[env]))
        elif format == "pycharm":
            print('        <env name="{}" value="{}" />'.format(env, os.environ[env]))
        else:
            raise Exception("unexpected: format is unknown: {}".format(format))


if __name__ == "__main__":

    if len(sys.argv) == 1:
        if ("OS" in os.environ) and (os.environ["OS"] == "Windows_NT"):
            envionment = "windows"
        else:
            format = "linux"
    elif len(sys.argv) == 2:
        if sys.argv[1] in ["windows", "linux", "powershell", "pycharm"]:
            format = sys.argv[1]
        else:
            usage()
    else:
        usage()

    identity_helpers.ensure_edge_environment_variables()

    print_env("IOTHUB_E2E_CONNECTION_STRING")
    print_env("IOTHUB_E2E_EDGEHUB_DNS_NAME")
    print_env("IOTHUB_E2E_EDGEHUB_DEVICE_ID")
    print_env("IOTHUB_E2E_REPO_ADDRESS")
    # print_env('IOTHUB_E2E_REPO_USER')
    # print_env('IOTHUB_E2E_REPO_PASSWORD')
    print_env("IOTHUB_E2E_EDGEHUB_CA_CERT")
    # print_env('IOTHUB_E2E_EDGE_PRIVATE_REGISTRY')
    # print_env('IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE')
    # print_env('IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE')
    
