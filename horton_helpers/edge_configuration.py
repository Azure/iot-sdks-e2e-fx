# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
import os


class EdgeConfiguration:
    """
    This class represents the edge hub configuration that is applied to an edgehub device under test.
    The caller will typically create an instance of this object, add modules using the add_module function,
    and finally use the get_module_config function to return a dictionary object that can be stringified to
    JSON and applied to an edgehub device.
    """

    def __init__(self):
        self.registryCredentials = {}

        if (
            False
            and len(os.environ.get("IOTHUB_E2E_EDGE_PRIVATE_REGISTRY", None) or "") > 0
        ):
            self.registryCredentials["edgebuilds"] = json.loads(
                os.environ["IOTHUB_E2E_EDGE_PRIVATE_REGISTRY"]
            )

        self.registryCredentials["hortoncontainers"] = {
            "address": os.environ["IOTHUB_E2E_REPO_ADDRESS"],
            "username": os.environ["IOTHUB_E2E_REPO_USER"],
            "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"],
        }

        if (
            False
            and len(os.environ.get("IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE", None) or "")
            > 0
        ):
            self.agentImage = os.environ["IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE"]
        else:
            self.agentImage = "mcr.microsoft.com/azureiotedge-agent:1.0"

        if (
            False
            and len(os.environ.get("IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE", None) or "") > 0
        ):
            self.hubImage = os.environ["IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE"]
        else:
            self.hubImage = "mcr.microsoft.com/azureiotedge-hub:1.0"

        self.config = {
            "moduleContent": {
                "$edgeAgent": {
                    "properties.desired": {
                        "schemaVersion": "1.0",
                        "runtime": {
                            "type": "docker",
                            "settings": {
                                "minDockerVersion": "v1.25",
                                "loggingOptions": "",
                                "registryCredentials": self.registryCredentials,
                            },
                        },
                        "systemModules": {
                            "edgeAgent": {
                                "type": "docker",
                                "settings": {
                                    "image": self.agentImage,
                                    "createOptions": "{}",
                                },
                                "env": {},
                            },
                            "edgeHub": {
                                "type": "docker",
                                "status": "running",
                                "restartPolicy": "always",
                                "settings": {
                                    "image": self.hubImage,
                                    "createOptions": '{\n  "HostConfig": {\n    "PortBindings": {\n      "8883/tcp": [\n        {\n          "HostPort": "8883"\n        }\n      ],\n      "443/tcp": [\n        {\n          "HostPort": "443"\n        }\n      ],\n      "5671/tcp": [\n        {\n          "HostPort": "5671"\n        }\n      ]\n    }\n  }\n}',
                                },
                                "env": {},
                            },
                        },
                        "modules": {},
                    }
                },
                "$edgeHub": {
                    "properties.desired": {
                        "schemaVersion": "1.0",
                        "routes": {},
                        "storeAndForwardConfiguration": {"timeToLiveSecs": 30},
                    }
                },
            }
        }

    def add_module_container(self, name, image, containerPort, hostPort):
        """
        Internal function which adds the module container to the edgehub configuration structure.
        """
        if containerPort != 0 and hostPort != 0:
            createOptions = {
                "HostConfig": {
                    "PortBindings": {
                        str(containerPort) + "/tcp": [{"HostPort": str(hostPort)}],
                        "22/tcp": [{"HostPort": hostPort + 100}],
                    }
                }
            }
        else:
            createOptions = {"HostConfig": {}}

        # BKTODO: We don't need NET_ADMIN and NET_RAW for all modules.  Only for ones
        # that require network disconneciton with iptables.  Not sure abou SYS_PTRACE.
        createOptions["HostConfig"]["CapAdd"] = ["SYS_PTRACE", "NET_ADMIN", "NET_RAW"]

        self.config["moduleContent"]["$edgeAgent"]["properties.desired"]["modules"][
            name
        ] = {
            "version": "1.0",
            "type": "docker",
            "status": "running",
            "restartPolicy": "always",
            "settings": {"image": image, "createOptions": json.dumps(createOptions)},
        }

    def add_routes_for_module(self, modName):
        """
        Internal function which adds various routes for testing the given module to the edgehub configuration.
        """
        self.config["moduleContent"]["$edgeHub"]["properties.desired"]["routes"].update(
            {
                modName
                + "Telemetry": "FROM /messages/modules/"
                + modName
                + "/outputs/telemetry INTO $upstream",
                modName
                + "Loopback": "FROM /messages/modules/"
                + modName
                + '/outputs/loopout INTO BrokeredEndpoint("/modules/'
                + modName
                + '/inputs/loopin")',
                modName
                + "ToFriend": "FROM /messages/modules/"
                + modName
                + '/outputs/toFriend INTO BrokeredEndpoint("/modules/friendMod/inputs/from'
                + modName
                + '")',
                modName
                + "FromFriend": "FROM /messages/modules/FriendMod/outputs/to"
                + modName
                + ' INTO BrokeredEndpoint("/modules/'
                + modName
                + '/inputs/fromFriend")',
                modName
                + "C2D": "FROM /messages/modules/"
                + modName
                + "/* INTO $upstream",
            }
        )

    def get_module_config(self):
        """
        Get an object that represents the edgehub device configuration.  This returned object can be stringified and set as the edgeHub device configuration
        """
        return self.config["moduleContent"]
