# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import posixpath
import drop
import logging
import get_stats
import json
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("system_control_app." + __name__)

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
            if self.path.startswith("/systemControl/setNetworkDestination/"):
                self.handle_set_network_destination()
            elif self.path.startswith("/systemControl/disconnectNetwork/"):
                self.handle_disconnect_network()
            elif self.path.startswith("/systemControl/reconnectNetwork"):
                self.handle_reconnect_network()
            else:
                self.send_response(404)
        except Exception:
            logger.error("exception in do_PUT", exc_info=True)
            self.send_response(500)

        self.end_headers()
        logger.info("done handling PUT for {}".format(self.path))

    def do_GET(self):
        logger.info("Received GET for{}".format(self.path))
        try:
            if self.path.startswith("/systemControl/systemStats/"):
                self.handle_get_system_stats()
            else:
                self.send_response(404)
        except Exception:
            logger.error("exception in do_GET", exc_info=True)
            self.send_response(500)

        self.end_headers()
        logger.info("done handling GET for {}".format(self.path))

    def handle_set_network_destination(self):
        # /systemControl/setNetworkDestination/<IP>/<transport>/
        logger.info("inside handle_set_network_destination")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 4:
            self.send_response(404)
        elif parts[3] not in drop.all_transports:
            self.send_response(404)
        else:
            self.do_set_network_destination(parts[2], parts[3])
            self.send_response(200)

    def handle_disconnect_network(self):
        # /systemControl/disconnectNetwork/<disconnect_type>/
        logger.info("inside handle_network_disconnect")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 3:
            self.send_response(404)
        elif parts[2] not in drop.all_disconnect_types:
            self.send_response(404)
        else:
            self.do_disconnect_network(parts[2])
            self.send_response(200)

    def handle_reconnect_network(self):
        # /systemControl/reconnectNetwork/
        logger.info("inside handle_reconnect_network")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 2:
            self.send_response(404)
        else:
            self.do_reconnect_network()
            self.send_response(200)

    def handle_get_system_stats(self):
        # /systemControl/systemStats/{pid}/
        logger.info("inside handle_reconnect_network")
        parts = split_path(self.path)
        logger.info("parts={}".format(parts))
        if len(parts) != 3:
            self.send_response(404)
        else:
            stats = self.get_system_stats(parts[2])
            self.send_response(200)
            self.send_header("Content-type", "text/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats, indent=2).encode("utf-8"))

    def do_set_network_destination(self, ip, transport):
        global destination_ip
        global client_transport
        destination_ip = ip
        client_transport = transport

    def do_disconnect_network(self, disconnect_type):
        drop.disconnect_port(disconnect_type, client_transport)

    def do_reconnect_network(self):
        drop.reconnect_port(client_transport)

    def get_system_stats(self, pid):
        system_uptime = get_stats.get_system_uptime()

        stats = {"system_uptime": system_uptime}

        try:
            stats.update(get_stats.get_memory_stats())
        except Exception:
            logger.info("Error getting memory stats")
            logger.info(traceback.format_exc())

        if pid:
            try:
                stats.update(get_stats.get_process_stats(pid))
            except Exception:
                logger.info("Error getting process stats")
                logger.info(traceback.format_exc())

        return stats


if __name__ == "__main__":
    run_server(handler_class=RequestHandler)
