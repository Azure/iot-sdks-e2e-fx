# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import connexion

# changed from from swagger_server import encoder
from . import encoder

# added imports in merge
import logging
import subprocess
import sys
import os


# added logging config in merge
logging.basicConfig(level=logging.INFO)
logging.getLogger("azure.iot.device").setLevel(level=logging.DEBUG)
logging.getLogger("paho").setLevel(level=logging.DEBUG)
logging.getLogger("werkzeug").setLevel(
    level=logging.WARNING
)  # info level can leak credentials into the log
logger = logging.getLogger(__name__)

# add subprocess launch during merge
this_module = sys.modules[__name__]
this_path = os.path.dirname(this_module.__file__)
try:
    system_control_pid = subprocess.Popen(
        "python {}/../../system_control_app/main.py".format(this_path).split(" ")
    )
except Exception:
    logger.error("Failed to launch system_control_app", exc_info=True)


def main():
    app = connexion.App(__name__, specification_dir="./swagger/")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        "swagger.yaml",
        arguments={"title": "Azure IOT End-to-End Test Wrapper Rest Api"},
    )
    # changed from app.run(port=8080)
    app.run(port=8080, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
