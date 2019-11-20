# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from http.server import HTTPServer, BaseHTTPRequestHandler
from six.moves import urllib
from urllib.parse import urlparse
import posixpath


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
            self.set_destination()
        elif self.path.startswith("/disconnect/"):
            self.disconnect()
        elif self.path.startswith("/reconnect/"):
            self.reconnect()
        elif self.path.startswith("/disconnect_after_c2d/"):
            self.disconnect_after_c2d()
        elif self.path.startswith("/disconnect_after_d2c/"):
            self.disconnect_after_d2c()
        else:
            self.send_response(404)

    def handle_set_destination(self):
        # /set_dest/<IP>/<port>/
        parts = split_path(self.path)
        if len(parts) != 3:
            self.send_response(404)
        else:
            ip = parts[1]
            try:
                port = int(parts[2])
            except ValueError:
                self.send_response(404)
                return
            self.do_set_destination(ip, port)

    def handle_disconnet(self):
        # /disconnect/<drop_mathod>/
        # BKTODO
        pass

    def handle_reconnect(self):
        # /reconnect/<drop_method>/
        # BKTODO
        pass

    def handle_disconnect_after_d2c(self):
        # /disconnect_after_c2d/<drop_method>/
        # BKTODO
        pass

    def handle_disconnet_after_c2d(self):
        # /disconnect_after_d2c/<drop_method>/
        # BKTODO
        pass

    def do_set_destination(self, ip, port):
        # BKTODO
        pass

    def do_disconnect(self, drop_method):
        # BKTODO
        pass

    def do_reconnect(self, drop_method):
        # BKTODO
        pass

    def do_disconnect_after_d2c(self, drop_method):
        # BKTODO
        pass

    def do_disconnect_after_c2d(self, drop_method):
        # BKTODO
        pass


if __name__ == "__main__":
    run_server(handler_class=RequestHandler)
