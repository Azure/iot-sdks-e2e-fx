# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
import os

# Single source of truth for the IoT Edge release line.  scripts/new/install-iotedge.sh
# pins the host aziot-edge daemon to this same line, so the daemon and the
# edgeAgent/edgeHub module images can never drift apart by accident.
EDGE_RELEASE_LINE = os.environ.get("IOTHUB_E2E_EDGE_RELEASE_LINE") or "1.6"


def _image_tag(image):
    """
    Return the tag portion of an image reference, or None if it has none.

    Only the final path segment is considered, since a registry host may itself
    contain a colon (myregistry:5000/azureiotedge-hub).  Digest-pinned
    references carry no version we can check.
    """
    last_segment = image.rsplit("/", 1)[-1]
    if "@" in last_segment:
        return None
    if ":" not in last_segment:
        return None
    return last_segment.rsplit(":", 1)[1]


def _verify_image_on_release_line(variable_name, image):
    """
    Reject an image override that is not on the configured release line.

    Running a daemon and module images from different lines is exactly the skew
    that produced weeks of intermittent EdgeHub twin failures, so a mismatch is
    an error rather than a warning.  Untagged and digest-pinned references carry
    no version to compare and are accepted; any other tag must be on the release
    line.  Set IOTHUB_E2E_EDGE_ALLOW_VERSION_SKEW=1 to allow a deliberate
    mismatch, including a private image whose tag does not encode a version.
    """
    if os.environ.get("IOTHUB_E2E_EDGE_ALLOW_VERSION_SKEW"):
        return

    tag = _image_tag(image)
    if tag is None:
        return

    if tag != EDGE_RELEASE_LINE and not tag.startswith(EDGE_RELEASE_LINE + "."):
        raise ValueError(
            "{}={} is not on the {} release line that the host aziot-edge daemon "
            "is pinned to (IOTHUB_E2E_EDGE_RELEASE_LINE). Mismatched daemon and "
            "module versions cause intermittent EdgeHub failures. Set "
            "IOTHUB_E2E_EDGE_ALLOW_VERSION_SKEW=1 if this is intentional.".format(
                variable_name, image, EDGE_RELEASE_LINE
            )
        )


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

        agentImage = os.environ.get("IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE", None) or ""
        if len(agentImage) > 0:
            _verify_image_on_release_line(
                "IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE", agentImage
            )
            self.agentImage = agentImage
        else:
            self.agentImage = (
                "mcr.microsoft.com/azureiotedge-agent:" + EDGE_RELEASE_LINE
            )

        hubImage = os.environ.get("IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE", None) or ""
        if len(hubImage) > 0:
            _verify_image_on_release_line("IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE", hubImage)
            self.hubImage = hubImage
        else:
            self.hubImage = "mcr.microsoft.com/azureiotedge-hub:" + EDGE_RELEASE_LINE

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
                                "env": {
                                    "DeviceScopeCacheRefreshRateSecs": {
                                        "value": "10"
                                    },
                                    "DeviceScopeCacheRefreshDelaySecs": {
                                        "value": "1"
                                    }
                                },
                            },
                        },
                        "modules": {},
                    }
                },
                "$edgeHub": {
                    "properties.desired": {
                        "schemaVersion": "1.0",
                        "routes": {},
                        "storeAndForwardConfiguration": {"timeToLiveSecs": 180},
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
                        "8040/tcp": [{"HostPort": 8140}],
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
                + "ToFriend": "FROM /messages/modules/"
                + modName
                + '/outputs/toFriend INTO BrokeredEndpoint("/modules/friendMod/inputs/from'
                + modName
                + '")',
                modName
                + "FromFriend": "FROM /messages/modules/friendMod/outputs/to"
                + modName
                + ' INTO BrokeredEndpoint("/modules/'
                + modName
                + '/inputs/fromFriend")',
                modName
                + "Default": "FROM /messages/modules/"
                + modName
                + "/* INTO $upstream",
            }
        )

    def get_module_config(self):
        """
        Get an object that represents the edgehub device configuration.  This returned object can be stringified and set as the edgeHub device configuration
        """
        return self.config["moduleContent"]
