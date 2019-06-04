#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import os
import base64
from pathlib import Path
from pprint import pprint
from identity_helpers import ensure_edge_environment_variables
from service_helper import Helper
import runtime_config_templates
import runtime_config_serializer
from containers import all_containers
import edgehub_factory
import adapters
import scenarios


runtime_config = None


def get_current_config():
    global runtime_config
    return runtime_config


def set_runtime_configuration(scenario, language, transport, local):
    global runtime_config

    if language == "ppdirect":
        runtime_config = runtime_config_templates.get_runtime_config_direct(scenario)
    else:
        runtime_config = runtime_config_templates.get_runtime_config(scenario)

    ensure_edge_environment_variables()

    # connection string for the IoTHub instance that is hosting your edgeHub instance.
    service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
    service_helper = Helper(service_connection_string)

    # deviceId for your edgeHub instance
    edge_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]

    # Are we using a gateway?  If so, collect the bits we need
    use_gateway_host = False
    if scenarios.USE_IOTEDGE_GATEWAYHOST in scenario.scenario_flags:
        use_gateway_host = True
        gateway_host_name = os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"]
        gateway_host_suffix = ";GatewayHostName=" + gateway_host_name
        if "IOTHUB_E2E_EDGEHUB_CA_CERT" in os.environ:
            runtime_config.ca_certificate = {
                "cert": base64.b64decode(
                    os.environ["IOTHUB_E2E_EDGEHUB_CA_CERT"]
                ).decode("utf-8")
            }
        else:
            raise Exception(
                "IOTHUB_E2E_EDGEHUB_CA_CERT missing from environment.  Do you need to run `eval $(../scripts/get-environment.sh)`?"
            )

    # DNS name for host that is running your edge hub instance
    host_for_rest_uri = os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"]
    # If we're on the actual machine, just use localhost instead
    config_yaml = Path("/etc/iotedge/config.yaml")
    if config_yaml.is_file():
        host_for_rest_uri = "localhost"

    # set up eventhub, the service client, and the registry client
    runtime_config.service.connection_string = service_connection_string
    runtime_config.registry.connection_string = service_connection_string
    runtime_config.eventhub.connection_string = service_connection_string

    # set up the device and module adapters that we're going to use
    if language == "ppdirect":
        container_under_test = all_containers["pythonpreview"]
    else:
        container_under_test = all_containers[language]

    hub = edgehub_factory.useExistingHubInstance(
        service_connection_string, edge_device_id
    )
    if getattr(runtime_config, "iotedge", None):
        runtime_config.iotedge.device_id = edge_device_id

    if getattr(runtime_config, "test_module", None):
        runtime_config.test_module.device_id = edge_device_id
        runtime_config.test_module.module_id = container_under_test.module_id
        runtime_config.test_module.connection_string = service_helper.get_module_connection_string(
            runtime_config.test_module.device_id, runtime_config.test_module.module_id
        )
        if use_gateway_host:
            runtime_config.test_module.connection_string += gateway_host_suffix
        if local:
            runtime_config.test_module.rest_uri = "http://localhost:" + str(
                container_under_test.local_port
            )
        else:
            runtime_config.test_module.rest_uri = (
                "http://"
                + host_for_rest_uri
                + ":"
                + str(container_under_test.host_port)
            )
        runtime_config.test_module.transport = transport
        if not runtime_config.test_module.connection_string:
            raise Exception(
                "test module has not been deployed.  You need to deploy your langauge module (even if you're testing locally)"
            )
        if local:
            runtime_config.test_module.connection_type = (
                runtime_config_templates.CONNECTION_STRING
            )

    friend_mod_rest_uri = (
        "http://" + host_for_rest_uri + ":" + str(all_containers["friend"].host_port)
    )
    if getattr(runtime_config, "friend_module", None):
        runtime_config.friend_module.device_id = edge_device_id
        runtime_config.friend_module.module_id = all_containers["friend"].module_id
        runtime_config.friend_module.connection_string = service_helper.get_module_connection_string(
            runtime_config.friend_module.device_id,
            runtime_config.friend_module.module_id,
        )

        if use_gateway_host:
            runtime_config.friend_module.connection_string += gateway_host_suffix
        runtime_config.friend_module.rest_uri = friend_mod_rest_uri
        if not runtime_config.friend_module.connection_string:
            raise Exception("friend module has not been deployed.")

    if getattr(runtime_config, "leaf_device", None):
        runtime_config.leaf_device.device_id = hub.leaf_device_id
        runtime_config.leaf_device.connection_string = hub.leaf_device_connection_string
        if use_gateway_host:
            runtime_config.leaf_device.connection_string += gateway_host_suffix
        if container_under_test.deviceImpl:
            runtime_config.leaf_device.rest_uri = runtime_config.test_module.rest_uri
        else:
            runtime_config.leaf_device.rest_uri = runtime_config.friend_module.rest_uri
        if not runtime_config.leaf_device.connection_string:
            raise Exception(
                "Leaf device does not appear to have an iothub identity.  You may need to re-run create-new-edgehub-device.sh"
            )

    # use the leaf device identity for our test_device tests for now.  This will change after we
    # update our deployment scripts
    if getattr(runtime_config, "test_device", None):
        runtime_config.test_device.device_id = hub.leaf_device_id
        runtime_config.test_device.connection_string = hub.leaf_device_connection_string
        if use_gateway_host:
            runtime_config.test_device.connection_string += gateway_host_suffix
        runtime_config.test_device.rest_uri = runtime_config.test_module.rest_uri
        if not runtime_config.test_device.connection_string:
            raise Exception(
                "Leaf device does not appear to have an iothub identity.  You may need to re-run create-new-edgehub-device.sh"
            )

    if language != "ppdirect":
        if container_under_test.registryImpl:
            runtime_config.registry.rest_uri = runtime_config.test_module.rest_uri
        else:
            runtime_config.registry.rest_uri = friend_mod_rest_uri

        if container_under_test.serviceImpl:
            runtime_config.service.rest_uri = runtime_config.test_module.rest_uri
        else:
            runtime_config.service.rest_uri = friend_mod_rest_uri

    if language == "ppdirect":
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


def get_test_module_wrapper_api():
    if getattr(adapters, "TestModuleClientWrapper", None):
        return adapters.TestModuleClientWrapper()
    else:
        return None
