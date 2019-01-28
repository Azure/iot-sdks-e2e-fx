#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


def print_message(message):
    """
    log the given message to stdout on the current process and also to stdout on any
    modules that are being used for the current test run.
    """
    print("PYTEST: " + message)
    # TODO: there is a seriously annoying circular dependency that make it necessary to do this inline.
    # otherwise, print_message imports the adapters, the adapters import the decorators, and the decorators import print_message
    from . import rest as rest_api_adapters
    rest_api_adapters.print_message(message)

