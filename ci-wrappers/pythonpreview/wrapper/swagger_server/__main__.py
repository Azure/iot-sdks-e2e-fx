#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import connexion
import logging
from . import encoder
try:
    import faulthandler
except ImportError:
    faulthandler = None


logging.basicConfig(level=logging.INFO)
logging.getLogger("paho").setLevel(level=logging.DEBUG)


def main():
    if faulthandler:
        faulthandler.enable()
    app = connexion.App(__name__, specification_dir="./swagger/")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        "swagger.yaml", arguments={"title": "IoT SDK Device &amp; Client REST API"}
    )
    app.run(port=8080, debug=True, use_reloader=False, threaded=True)

if __name__ == '__main__':
    main()

