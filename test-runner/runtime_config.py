#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import os
import base64
from pathlib import Path
from pprint import pprint
from identity_helpers import ensure_edge_environment_variables
import runtime_config_templates
import runtime_config_serializer
from containers import all_containers
import edgehub_factory
import adapters
import scenarios


class EdgeHubRuntimeConfig:
    def __init__(self):
        self.service = None
        self.registry = None
        self.iotedge = None
        self.test_module = None
        self.friend_module = None
        self.leaf_device = None
        self.eventhub = None
        self.ca_certificate = None


class IotHubRuntimeConfig:
    def __init__(self):
        self.service = None
        self.registry = None
        self.test_module = None
        self.eventhub = None


runtime_config = None

iothub_scenarios = ["iothub_module", "iothub_device"]
edgehub_scenarios = ["edgehub_module", "edgehub_module_fi"]


def get_current_config():
    global runtime_config
    return runtime_config


def set_runtime_configuration(scenario, language, transport, local):
    global runtime_config

    runtime_config = EdgeHubRuntimeConfig()

    direct_to_iothub = True
    if scenarios.USE_IOTEDGE_GATEWAYHOST in scenario.scenario_flags:
        direct_to_iothub = False

    ensure_edge_environment_variables()

    # connection string for the IoTHub instance that is hosting your edgeHub instance.
    service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]

    # deviceId for your edgeHub instance
    edge_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]

    # DNS name for host that is running your edge hub instance
    host_for_rest_uri = os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"]
    gateway_host_name = os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"]

    # If we're on the actual machine, just use localhost instead

    config_yaml = Path("/etc/iotedge/config.yaml")
    if config_yaml.is_file():
        host_for_rest_uri = "localhost"

    # CA certificate for you edgeHub instance.
    # only used in some SDKs if friend_module_connect_from_environment == False
    #
    # Other SDKs may need this added to the "Trusted Root Certificate Authorities"
    # portion of the trust store if you're using connect_from_environment == False.
    # (You know who you are)
    #
    # retrived from edge-e2e/scripts/get_ca_cert.sh
    if "IOTHUB_E2E_EDGEHUB_CA_CERT" in os.environ:
        runtime_config.ca_certificate = {
            "cert": base64.b64decode(os.environ["IOTHUB_E2E_EDGEHUB_CA_CERT"]).decode(
                "utf-8"
            )
        }

    runtime_config.iotedge = runtime_config_templates.IotEdgeDevice()
    runtime_config.friend_module = runtime_config_templates.EdgeHubModuleRest(
        "FriendModuleClient"
    )
    runtime_config.eventhub = runtime_config_templates.EventHubDirect()

    if language == "ppdirect":
        container_under_test = all_containers["pythonpreview"]
        runtime_config.service = runtime_config_templates.IotHubServiceDirect()
        runtime_config.registry = runtime_config_templates.IotHubRegistryDirect()
        runtime_config.test_module = runtime_config_templates.EdgeHubModuleDirect(
            "TestModuleClient"
        )
        runtime_config.leaf_device = runtime_config_templates.EdgeHubLeafDeviceRest(
            "LeafDeviceClient"
        )
    else:
        container_under_test = all_containers[language]
        runtime_config.service = runtime_config_templates.IotHubServiceRest()
        runtime_config.registry = runtime_config_templates.IotHubRegistryRest()
        runtime_config.test_module = runtime_config_templates.EdgeHubModuleRest(
            "TestModuleClient"
        )
        runtime_config.leaf_device = runtime_config_templates.EdgeHubLeafDeviceRest(
            "LeafDeviceClient"
        )

    hub = edgehub_factory.useExistingHubInstance(
        service_connection_string, edge_device_id
    )

    runtime_config.service.connection_string = service_connection_string
    runtime_config.registry.connection_string = service_connection_string
    runtime_config.eventhub.connection_string = service_connection_string

    runtime_config.iotedge.device_id = edge_device_id

    runtime_config.test_module.device_id = edge_device_id
    runtime_config.test_module.module_id = container_under_test.module_id
    runtime_config.test_module.connection_string = (
        container_under_test.connection_string
    )
    if local:
        runtime_config.test_module.rest_uri = "http://localhost:" + str(
            container_under_test.local_port
        )
    else:
        runtime_config.test_module.rest_uri = (
            "http://" + host_for_rest_uri + ":" + str(container_under_test.host_port)
        )
    runtime_config.test_module.transport = transport
    runtime_config.test_module.language = language

    runtime_config.friend_module.device_id = edge_device_id
    runtime_config.friend_module.module_id = all_containers["friend"].module_id
    runtime_config.friend_module.connection_string = all_containers[
        "friend"
    ].connection_string
    runtime_config.friend_module.rest_uri = (
        "http://" + host_for_rest_uri + ":" + str(all_containers["friend"].host_port)
    )

    runtime_config.leaf_device.device_id = hub.leaf_device_id
    runtime_config.leaf_device.connection_string = hub.leaf_device_connection_string
    if container_under_test.deviceImpl:
        runtime_config.leaf_device.rest_uri = runtime_config.test_module.rest_uri
    else:
        runtime_config.leaf_device.rest_uri = runtime_config.friend_module.rest_uri

    if not runtime_config.test_module.connection_string:
        raise Exception(
            "test module has not been deployed.  You need to deploy your langauge module (even if you're testing locally)"
        )
    if not runtime_config.friend_module.connection_string:
        raise Exception("friend module has not been deployed.")
    if not runtime_config.leaf_device.connection_string:
        raise Exception(
            "Leaf device does not appear to have an iothub identity.  You may need to re-run create-new-edgehub-device.sh"
        )

    if container_under_test.registryImpl:
        runtime_config.registry.rest_uri = runtime_config.test_module.rest_uri
    else:
        runtime_config.registry.rest_uri = runtime_config.friend_module.rest_uri

    if container_under_test.serviceImpl:
        runtime_config.service.rest_uri = runtime_config.test_module.rest_uri
    else:
        runtime_config.service.rest_uri = runtime_config.friend_module.rest_uri

    if not direct_to_iothub:
        # route all of our devices through edgeHub if necessary
        gatewayHostSuffix = ";GatewayHostName=" + gateway_host_name
        runtime_config.test_module.connection_string += gatewayHostSuffix
        runtime_config.friend_module.connection_string += gatewayHostSuffix
        runtime_config.leaf_device.connection_string += gatewayHostSuffix
    else:
        runtime_config.ca_certificate = {}  # must be an empty dictionary
        runtime_config.test_module.connection_type = (
            runtime_config_templates.CONNECTION_STRING
        )
        runtime_config.friend_module.connection_type = (
            runtime_config_templates.CONNECTION_STRING
        )

    if local and not direct_to_iothub:
        runtime_config.test_module.connection_type = (
            runtime_config_templates.CONNECTION_STRING
        )

    if language == "ppdirect":
        if not direct_to_iothub:
            runtime_config.test_module.connection_type = (
                runtime_config_templates.CONNECTION_STRING
            )

    for object_name in dir(runtime_config):
        test_obj = getattr(runtime_config, object_name)
        if getattr(test_obj, "test_object_type", None):
            adapter_type = getattr(test_obj, "adapter_type", None)
            if not adapter_type:
                pass
            elif adapter_type == runtime_config_templates.REST_ADAPTER:
                adapters.add_rest_adapter(
                    name=test_obj.api_name,
                    api_surface=test_obj.api_surface,
                    uri=test_obj.rest_uri,
                )
            elif adapter_type == runtime_config_templates.DIRECT_AZURE_ADAPTER:
                adapters.add_direct_azure_rest_adapter(
                    name=test_obj.api_name, api_surface=test_obj.api_surface
                )
            elif adapter_type == runtime_config_templates.DIRECT_PYTHON_SDK_ADAPTER:
                adapters.add_direct_python_sdk_adapter(
                    name=test_obj.api_name, api_surface=test_obj.api_surface
                )

    pprint(runtime_config_serializer.obj_to_dict(runtime_config))
