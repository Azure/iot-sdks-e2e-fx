# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from . import rest
from . import direct_azure_rest


api_surfaces = [
    "module_client",
    "device_client",
    "wrapper",
    "service",
    "registry",
    "eventhub",
    "system_control",
]


def create_adapter(adapter_address, api_surface):
    if api_surface not in api_surfaces:
        raise ValueError("api_surface {} invalid".format(api_surface))

    if adapter_address == "direct_rest":
        return create_direct_azure_adapter(api_surface)
    elif adapter_address.startswith("http"):
        return create_rest_adapter(adapter_address, api_surface)
    else:
        raise ValueError("adapter_address {} invalid".format(adapter_address))


def create_direct_azure_adapter(api_surface):
    if api_surface == "service":
        return direct_azure_rest.ServiceApi()
    elif api_surface == "registry":
        return direct_azure_rest.RegistryApi()
    elif api_surface == "eventhub":
        return direct_azure_rest.EventHubApi()
    else:
        raise ValueError("direct_azure adapter for {} invalid".format(api_surface))


def create_rest_adapter(adapter_address, api_surface):
    if api_surface == "module_client":
        return rest.ModuleApi(adapter_address)
    elif api_surface == "device_client":
        return rest.DeviceApi(adapter_address)
    elif api_surface == "wrapper":
        return rest.ControlApi(adapter_address)
    elif api_surface == "service":
        return rest.ServiceApi(adapter_address)
    elif api_surface == "registry":
        return rest.RegistryApi(adapter_address)
    elif api_surface == "system_control":
        return rest.SystemControlApi(adapter_address)
    else:
        raise ValueError("rest adapter for {} invalid".format(api_surface))
