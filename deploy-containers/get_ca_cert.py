# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from horton_settings import settings
import base64


def get_ca_cert():
    if settings.iotedge.device_id:
        encoded_cert = settings.iotedge.ca_cert_base64
        print(base64.b64decode(encoded_cert).decode("ascii"))
    else:
        raise Exception(
            "No CA cert specificed in settings.  Do you need to run deploy.py or get_credentials.py?"
        )


if __name__ == "__main__":
    get_ca_cert()
