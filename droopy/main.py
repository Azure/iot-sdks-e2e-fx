# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from http.server import HTTPServer, BaseHTTPRequestHandler
from six.moves import urllib
from urllib.parse import urlparse
import posixpath
import drop

client_transport = ""
destination_ip = ""


def run_server(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
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
    def do_GET(self):
        if self.path.startswith("/set_dest/"):
            self.handle_set_destination()
        elif self.path.startswith("/disconnect/"):
            self.handle_disconnect()
        elif self.path.startswith("/reconnect/"):
            self.handle_reconnect()
        elif self.path.startswith("/disconnect_after_c2d/"):
            self.handle_disconnect_after_c2d()
        elif self.path.startswith("/disconnect_after_d2c/"):
            self.handle_disconnect_after_d2c()
        else:
            self.send_response(404)

    def handle_set_destination(self):
        # /set_dest/<IP>/<transport>/
        parts = split_path(self.path)
        if len(parts) != 3:
            self.send_response(404)
        elif parts[2] not in drop.all_transports:
            self.send_response(404)
        else:
            self.do_set_destination(parts[1], parts[2])

    def handle_disconnet(self):
        # /disconnect/<drop_mathod>/
        parts = split_path(self.path)
        if len(parts) != 2:
            self.send_response(404)
        elif parts[1] not in drop.all_disconnect_types:
            self.send_response(404)
        else:
            self.do_disconnect(parts[1])

    def handle_reconnect(self):
        # /reconnect/<drop_method>/
        parts = split_path(self.path)
        if len(parts) != 2:
            self.send_response(404)
        elif parts[1] not in drop.all_disconnect_types:
            self.send_response(404)
        else:
            self.do_reconnect(parts[1])

    def handle_disconnet_after_c2d(self):
        # /disconnect_after_c2d/<drop_method>/
        parts = split_path(self.path)
        if len(parts) != 2:
            self.send_response(404)
        elif parts[1] not in drop.all_disconnect_types:
            self.send_response(404)
        else:
            self.do_disconnect_after_c2d(parts[1])

    def handle_disconnect_after_d2c(self):
        # /disconnect_after_d2c/<drop_method>/
        parts = split_path(self.path)
        if len(parts) != 2:
            self.send_response(404)
        elif parts[1] not in drop.all_disconnect_types:
            self.send_response(404)
        else:
            self.do_disconnect_after_d2c(parts[1])

    def do_set_destination(self, ip, transport):
        global destination_ip
        global client_transport
        destination_ip = ip
        client_transport = transport
        self.send_reponse(200)

    def do_disconnect(self, drop_method):
        # BKTODO
        pass

    def do_reconnect(self, drop_method):
        # BKTODO
        pass

    def do_disconnect_after_c2d(self, drop_method):
        # BKTODO
        pass

    def do_disconnect_after_d2c(self, drop_method):
        # BKTODO
        pass


if __name__ == "__main__":
    run_server(handler_class=RequestHandler)
