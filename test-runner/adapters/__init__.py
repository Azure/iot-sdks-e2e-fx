#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import sys
from .decorators import *
from . import rest as rest_adapters
from . import direct_azure_rest as direct_azure_rest_adapters
from .print_message import print_message

try:
    from . import direct_python_sdk as direct_python_sdk_adapters
except ModuleNotFoundError:
    # It's OK to fail this.  The import will only succeed if the use has the
    # iot sdks pip packages installed, and the import is only necessary if
    # you're actually using the pp_direct adapters.
    print("Failed to load direct_python_sdk_adapters.  Skipping.")

this_module = sys.modules[__name__]

"""
This file implements an uncommon way of creating objects. Instead of exporting object
constructor functions from this module, we export functions that "add adapters".  These
adapter objects are objects that let you call code under test using _some_ RPC mechanism
depending on the type of adapter, or no RPC mechanism if you want to call the test code
directly.  By adding an adapter using a given type of RPC, you are basically adding
a factory that can create that adapter. This way, functions like add_rest_adapter are
like factory factories.  That is, when you call add_rest_adapter, you're creating an
object factory and exporting it from this module.

This may feel like a strange way of creating objects, but this allows us to dynamically
add test objects based on runtime configuration.  As of today, the only kind of adapter
is a REST adapter, but more types of adapters will be added soon, and this pattern will
allow us to make the type of wrapper opaque to the test code.  The data-driven way that
this function creates factories allows us to easily add more test objects in the future,
based entirely on configuration data.
"""


def add_rest_adapter(name, api_surface, uri):
    """
    Adds a REST adapter with the given name, using the given surface, at the given URI.
    `name` is the name of the adapter factory that will be exported from this module,
            so if `name` is "ModuleApiClient", this function will add a factory function
            called "ModuleApiClient" to this module's list of exports.  This way, after
            an adapter called "ModuleApiClient" is added using this function, "callers
            will be able to create an adapter by importing adapters.ModuleApiClient and
            calling the returned funciton.
    `api_surface` is the name of the api object exported from the `REST` package.  If
            `api_surface` is "module_api" then the factory will return a module_api object.
    `uri` is the uri for the REST endpoint that implements the given api
    """
    print(
        "Adding REST adapter for {} using the {} api at uri {}".format(
            name, api_surface, uri
        )
    )

    def _add_rest_factory(factory_name, factory_surface):
        AdapterClass = getattr(rest_adapters, factory_surface)

        def factory():
            object = AdapterClass(uri)
            return object

        setattr(this_module, factory_name, factory)

    _add_rest_factory(name, api_surface)
    _add_rest_factory(name + "Wrapper", "WrapperApi")
    rest_adapters.add_rest_uri(uri)


def add_direct_azure_rest_adapter(name, api_surface):
    print("Adding direct Azure rest adapter for {}".format(name))
    AdapterClass = getattr(direct_azure_rest_adapters, api_surface)
    setattr(this_module, name, AdapterClass)


def add_direct_python_sdk_adapter(name, api_surface):
    print(
        "Adding direct Python SDK adapter for {} using the {} api".format(
            name, api_surface
        )
    )
    # if this line excepts, it's probably because the import of direct_python_sdk_adapters
    # failed, and that's probably because you don't have the iot sdk packages installed.
    AdapterClass = getattr(direct_python_sdk_adapters, api_surface)
    setattr(this_module, name, AdapterClass)
    WrapperAdapterClass = getattr(direct_python_sdk_adapters, "WrapperApi")
    setattr(this_module, name + "Wrapper", WrapperAdapterClass)


def cleanup_test_objects():
    """
    Function to call into all adapter objects and perform cleanup on the test objects
    that those adapters are responsible for.
    """
    rest_adapters.cleanup_test_objects()
    direct_azure_rest_adapters.cleanup_test_objects()
    if getattr(this_module, "direct_python_sdk_adapters", None):
        direct_python_sdk_adapters.cleanup_test_objects()
