# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import connexion
# changed from from swagger_server import encoder
from . import encoder
# added logging config in merge
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("azure.iot.device").setLevel(level=logging.DEBUG)
logging.getLogger("paho").setLevel(level=logging.DEBUG)
logging.getLogger("werkzeug").setLevel(level=logging.WARNING) # info level can leak credentials into the log


def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Azure IOT End-to-End Test Wrapper Rest Api'})
    # changed from app.run(port=8080)
    app.run(port=8080, debug=True, use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()
