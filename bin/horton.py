# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import argparse
from deploy import horton_deploy, horton_undeploy, horton_get_credentials

try:
    from build import horton_build
except ModuleNotFoundError:
    # Fails on Windows.  Exclude this option
    horton_build = None

subcommands = {
    "deploy": horton_deploy,
    "undeploy": horton_undeploy,
    "get_credentials": horton_get_credentials,
}

if horton_build:
    subcommands["build"] = horton_build


def set_command_args(parser):
    parser.description = "Horton control app"
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    for command in subcommands:
        subcommand_module = subcommands[command]
        subparser = subparsers.add_parser(
            command, help=subcommand_module.get_description()
        )
        subcommand_module.set_command_args(subparser)


def handle_command_args(args):
    subcommand_module = subcommands[args.command]
    subcommand_module.handle_command_args(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="horton")
    set_command_args(parser)
    args = parser.parse_args()
    handle_command_args(args)
