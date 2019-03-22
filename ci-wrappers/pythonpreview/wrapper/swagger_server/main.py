#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import connexion
import faulthandler
import logging


logging.basicConfig(level=logging.INFO)
logging.getLogger("paho").setLevel(level=logging.DEBUG)

from . import encoder

def main():
    faulthandler.enable()
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'IoT SDK Device &amp; Client REST API'})
    app.run(port=8080, debug=True, use_reloader=False, threaded=True)
