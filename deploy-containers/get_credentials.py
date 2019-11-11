# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from iothub_service_helper import IoTHubServiceHelper
from horton_settings import settings
import base64
import glob
import utilities


iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)


def get_edge_ca_cert_base64():
    filename = glob.glob("/var/lib/iotedge/hsm/certs/edge_owner_ca*.pem")[0]
    cert = utilities.run_shell_command("sudo -n cat {}".format(filename))
    return base64.b64encode("\n".join(cert).encode("ascii")).decode("ascii")


def populate_credentials():

    if settings.iotedge.device_id:
        settings.iotedge.ca_cert_base64 = get_edge_ca_cert_base64()

    for device in (settings.leaf_device, settings.test_device):
        if device.device_id:
            if device.connection_type.startswith("connection_string"):
                device.connection_string = iothub_service_helper.get_device_connection_string(
                    device.device_id
                )
                if device.connection_type.endswith("_with_edge_gateway"):
                    device.connection_string += ";GatewayHostName={}".format(
                        settings.iotedge.hostname
                    )
                print(
                    "Added connection string for {} device {}".format(
                        device.name, device.device_id
                    )
                )

    for module in (settings.test_module, settings.friend_module):
        if module.device_id and module.module_id:

            if (
                module.connection_type.startswith("connection_string")
                or module.connection_type == "environment"
            ):
                module.connection_string = iothub_service_helper.get_module_connection_string(
                    module.device_id, module.module_id
                )
                if (
                    module.connection_type.endswith("_with_edge_gateway")
                    or module.connection_type == "environment"
                ):
                    module.connection_string += ";GatewayHostName={}".format(
                        settings.iotedge.hostname
                    )

                print(
                    "Added connection string for {} module {},{}".format(
                        module.name, module.device_id, module.module_id
                    )
                )
    settings.save()


if __name__ == "__main__":
    populate_credentials()
