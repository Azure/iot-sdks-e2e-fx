#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from identity_helpers import ensure_edge_environment_variables
from connection_string import connection_string_to_sas_token
from edgehub_factory import useExistingHubInstance
from containers import all_containers
import os
import sys
import string
import argparse

ensure_edge_environment_variables()

parser = argparse.ArgumentParser(description="deploy containers for testing")
parser.add_argument("--all", action="store_true", help="deploy all containers")
for container_name in all_containers:
    parser.add_argument(
        "--" + container_name,
        help="deploy " + container_name + " container.",
        metavar="image_name",
        nargs="?",
        const=all_containers[container_name].lkg_image,
    )
args = parser.parse_args()

for container_name in all_containers:
    if not getattr(args, container_name):
        if args.all or all_containers[container_name].required:
            setattr(args, container_name, all_containers[container_name].lkg_image)

if not (
    "IOTHUB_E2E_REPO_ADDRESS" in os.environ
    and "IOTHUB_E2E_REPO_USER" in os.environ
    and "IOTHUB_E2E_REPO_PASSWORD" in os.environ
):
    print(
        "Error: Docker container repository credentials are not set in IOTHUB_E2E_REPO* environment variables."
    )
    sys.exit(1)

service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
host = connection_string_to_sas_token(service_connection_string)["host"]
edge_hub_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]

print("Operating with device {} on on hub {}".format(edge_hub_device_id, host))
print()
print("Deploying the following containers:")
containers_to_deploy = set()
for container_name in all_containers:
    if hasattr(args, container_name) and getattr(args, container_name):
        container = all_containers[container_name]
        container.image_to_deploy = getattr(args, container_name)
        print("{:>10}: {}".format(container_name, container.image_to_deploy))
        containers_to_deploy.add(container_name)

hub = useExistingHubInstance(service_connection_string, edge_hub_device_id)

containers = ",".join(containers_to_deploy)
hub.deployModules(containers)
