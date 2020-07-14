# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import posixpath
import drop
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("net_control." + __name__)

default_port = 8040
client_transport = ""
destination_ip = ""


def run_server(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    logger.info("listening on port 8040")
    server_address = ("", 8040)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def split_path(path):
    result = []
    tmp = posixpath.normpath(path)
    while tmp != "/":
        (tmp, item) = posixpath.split(tmp)
        result.insert(0, item)
    return result


class RequestHandler(BaseHTTPRequestHandler):
    def do_PUT(self):
        logger.info("Received PUT for {}".format(self.path))
        try:
            if self.path.startswith("/net/setDestination/"):
                self.handle_set_destination()
            elif self.path.startswith("/net/disconnect/"):
                self.handle_disconnect()
            elif self.path.startswith("/net/reconnect"):
                self.handle_reconnect()
            else:
                self.send_response(404)
        except Exception:
            logger.error("exception in do_PUT", exc_info=True)
            self.send_response(500)

        self.end_headers()
        logger.info("done handling PUT for {}".format(self.path))

    def handle_set_destination(self):
        # /net/setDestination/<IP>/<transport>/
        logger.info("inside handle_set_destination")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 4:
            self.send_response(404)
        elif parts[3] not in drop.all_transports:
            self.send_response(404)
        else:
            self.do_set_destination(parts[2], parts[3])
            self.send_response(200)

    def handle_disconnect(self):
        # /net/disconnect/<disconnect_type>/
        logger.info("inside handle_disconnect")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 3:
            self.send_response(404)
        elif parts[2] not in drop.all_disconnect_types:
            self.send_response(404)
        else:
            self.do_disconnect(parts[2])
            self.send_response(200)

    def handle_reconnect(self):
        # /net/reconnect/
        logger.info("inside handle_reconnect")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 2:
            self.send_response(404)
        else:
            self.do_reconnect()
            self.send_response(200)

    def do_set_destination(self, ip, transport):
        global destination_ip
        global client_transport
        destination_ip = ip
        client_transport = transport
        self.send_response(200)

    def do_disconnect(self, disconnect_type):
        drop.disconnect_port(disconnect_type, client_transport)

    def do_reconnect(self):
        drop.reconnect_port(client_transport)


if __name__ == "__main__":
    run_server(handler_class=RequestHandler)
