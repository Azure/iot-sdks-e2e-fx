# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import argparse
from . import utilities


def get_description():
    return "Remove horton deployment"


def set_command_args(parser):
    parser.description = get_description()


def handle_command_args(args):
    utilities.remove_old_instances()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="horton_undeploy")
    set_command_args(parser)
    args = parser.parse_args()
    handle_command_args(args)
