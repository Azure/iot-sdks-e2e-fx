#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import conftest
import os
import sys
import base64
import edgehub_factory as edgehub_factory
from containers import all_containers
from get_environment_variables import verifyEnvironmentVariables
import adapters

verifyEnvironmentVariables()


# --------------------------------------------------------------------------------------
# execution settings that you might want to modify for your run
# --------------------------------------------------------------------------------------

# Transport to use for the module-under-test.  One of 'mqtt', 'mqttws', 'amqp', 'amqpws', or 'http'
# (these values are valid, but may not be implemented.)
test_module_transport = "mqtt"

# Transport to use for the friend module.  One of 'mqtt', 'mqttws', 'amqp', 'amqpws', or 'http'
# (these values are valid, but may not be implemented.)
friend_module_transport = "mqtt"

# Transport to use for the leaf device.  One of 'mqtt', 'mqttws', 'amqp', 'amqpws', or 'http'
leaf_device_transport = "mqtt"

# If True, uses the fromEnvironment function to connect.  If False, uses the connection string and cert
test_module_connect_from_environment = True

# If True, uses the fromEnvironment function to connect.  If False, uses the connection string and cert
friend_module_connect_from_environment = True

# --------------------------------------------------------------------------------------
# execution settings that come directly from environment variables.
# --------------------------------------------------------------------------------------

if "IOTHUB_E2E_CONNECTION_STRING" not in os.environ:
    print(
        "ERROR: Iothub connection string not set in IOTHUB_E2E_CONNECTION_STRING environment variable."
    )
    sys.exit(1)

if "IOTHUB_E2E_EDGEHUB_DEVICE_ID" not in os.environ:
    print(
        "ERROR: Edge device ID not set in IOTHUB_E2E_EDGEHUB_DEVICE_ID environment variable.  You can use CreateNewEdgeHubDevice.cmd/sh to create a new device"
    )
    sys.exit(1)

if "IOTHUB_E2E_EDGEHUB_DNS_NAME" not in os.environ:
    print(
        "ERROR: DNS name of edge service VM not set in IOTHUB_E2E_EDGEHUB_DNS_NAME environment variable."
    )
    sys.exit(1)

# connection string for the IoTHub instance that is hosting your edgeHub instance.
service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]

# deviceId for your edgeHub instance
edge_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]

# DNS name for host that is running your edge hub instance
edge_hub_host = os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"]

# CA certificate for you edgeHub instance.
# only used in some SDKs if friend_module_connect_from_environment == False
#
# Other SDKs may need this added to the "Trusted Root Certificate Authorities"
# portion of the trust store if you're using connect_from_environment == False.
# (You know who you are)
#
# retrived from edge-e2e/scripts/get_ca_cert.sh
ca_certificate = None
if "IOTHUB_E2E_EDGEHUB_CA_CERT" in os.environ:
    ca_certificate = {
        "cert": base64.b64decode(os.environ["IOTHUB_E2E_EDGEHUB_CA_CERT"]).decode(
            "utf-8"
        )
    }

# --------------------------------------------------------------------------------------
# Environment settings that come from the hub or from command line args
# (these can't be set until after pytest_collection_modifyitems runs, and that
# happens fairly late, so we leave them set as None until setUpExecutionEnvironment
# can be run
# --------------------------------------------------------------------------------------

# moduleId for the module under test
module_id = None

# moduleId for the friend module
friend_module_id = None

# device ID for leaf device
leaf_device_id = None

# connection string for the module that is being testes
test_module_connection_string = None

# connection string for the bounceback module
friend_module_connection_string = None

# connection string for leaf device
leaf_device_connection_string = None

# URI to use for the module API under test
test_module_uri = None

# URI for the bounceback module
friend_module_uri = None

# URI for the bounceback device
leaf_device_uri = None

# URI to use for the registry API under test
registry_uri = None

# URI to use for the service client API under test
service_client_uri = None

# language being tested
language = None


def setupExecutionEnvironment():
    """
  Finish getting details needed for executing tests. This includes information that comes from the service,
  such as connection strings, and also endpoint URIs that can't be built until after command lines are parsed
  in conftest.py (which happens after all modules are loaded)
  """
    global leaf_device_id, leaf_device_connection_string
    global module_id, test_module_connection_string
    global friend_module_id, friend_module_connection_string
    global test_module_uri, friend_module_uri, leaf_device_uri
    global registry_uri, service_client_uri
    global test_module_connect_from_environment, friend_module_connect_from_environment
    global ca_certificate
    global test_module_transport, friend_module_transport
    global language

    if conftest.language == "ppdirect":
        container_under_test = all_containers["pythonpreview"]
    else:
        container_under_test = all_containers[conftest.language]

    hub = edgehub_factory.useExistingHubInstance(
        service_connection_string, edge_device_id
    )

    module_id = container_under_test.module_id

    friend_module_id = all_containers["friend"].module_id

    leaf_device_id = hub.leaf_device_id

    test_module_connection_string = container_under_test.connection_string

    friend_module_connection_string = all_containers["friend"].connection_string

    leaf_device_connection_string = hub.leaf_device_connection_string

    if test_module_connection_string is None or test_module_connection_string == "":
        raise Exception(
            "test module has not been deployed.  You need to deploy your langauge module (even if you're testing locally)"
        )
    if friend_module_connection_string is None or friend_module_connection_string == "":
        raise Exception("friend module has not been deployed.")
    if leaf_device_connection_string is None or leaf_device_connection_string == "":
        raise Exception(
            "Leaf device does not appear to have an iothub identity.  You may need to re-run create-new-edgehub-device.sh"
        )

    if conftest.local:
        edge_test_container = "http://localhost:" + str(container_under_test.local_port)
    else:
        edge_test_container = (
            "http://" + edge_hub_host + ":" + str(container_under_test.host_port)
        )

    edge_friend_container = (
        "http://" + edge_hub_host + ":" + str(all_containers["friend"].host_port)
    )

    if not conftest.direct_to_iothub:
        # route all of our devices through edgeHub if necessary
        gatewayHostSuffix = ";GatewayHostName=" + edge_hub_host
        test_module_connection_string = (
            test_module_connection_string + gatewayHostSuffix
        )
        friend_module_connection_string = (
            friend_module_connection_string + gatewayHostSuffix
        )
        leaf_device_connection_string = (
            leaf_device_connection_string + gatewayHostSuffix
        )
    else:
        # no certificate if we're going straight to iothub
        ca_certificate = {}
        test_module_connect_from_environment = False
        friend_module_connect_from_environment = False

    test_module_uri = edge_test_container

    friend_module_uri = edge_friend_container

    leaf_device_uri = edge_test_container
    if container_under_test.deviceImpl is False:
        leaf_device_uri = edge_friend_container

    registry_uri = edge_test_container
    if container_under_test.registryImpl is False:
        registry_uri = edge_friend_container

    service_client_uri = edge_test_container
    if container_under_test.serviceImpl is False:
        service_client_uri = edge_friend_container

    if conftest.test_module_use_connection_string:
        test_module_connect_from_environment = False

    test_module_transport = conftest.transport
    #  friend_module_transport = conftest.transport

    def friendly_uri(uri):
        if uri == edge_test_container:
            return uri + " (module under test)"
        elif uri == edge_friend_container:
            return uri + " (friend container)"
        else:
            return uri + " (some other container)"

    language = conftest.language

    if language == "ppdirect":
        adapters.add_direct_iot_sdk_adapter(
            name="TestModuleClient", api_surface="ModuleApi"
        )
    else:
        adapters.add_rest_adapter(
            name="TestModuleClient", api_surface="ModuleApi", uri=test_module_uri
        )
    adapters.add_rest_adapter(
        name="FriendModuleClient", api_surface="ModuleApi", uri=friend_module_uri
    )
    adapters.add_rest_adapter(
        name="LeafDeviceClient", api_surface="DeviceApi", uri=leaf_device_uri
    )
    adapters.add_rest_adapter(
        name="RegistryClient", api_surface="RegistryApi", uri=registry_uri
    )
    adapters.add_rest_adapter(
        name="ServiceClient", api_surface="ServiceApi", uri=service_client_uri
    )
    adapters.add_direct_eventhub_adapter()

    print("Run Parameters:")
    print("  language:             {}".format(language))
    print("  module_id:            {}".format(module_id))
    print("  friend_module_id:     {}".format(friend_module_id))
    print("  leaf_device_id:       {}".format(leaf_device_id))
    print("  using environment:    {}".format(test_module_connect_from_environment))
    print("  test transport:       {}".format(test_module_transport))
    print("  friend transport:     {}".format(friend_module_transport))
    print(
        "  destination:          {}".format(
            "iothub" if conftest.direct_to_iothub else "edgehub"
        )
    )
