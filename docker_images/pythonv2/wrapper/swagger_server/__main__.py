#!/usr/bin/env python

import connexion

from swagger_server import encoder


def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Azure IOT End-to-End Test Wrapper Rest Api'})
    app.run(port=8080)


if __name__ == '__main__':
    main()
