# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import subprocess

logger = logging.getLogger(__name__)

do_async = False

all_disconnect_types = ["DROP", "REJECT"]
mqtt_port = 8883


def log_message(msg):
    if "message" in msg:
        print(msg["message"])
    else:
        print(str(msg))


def set_flags(flags):
    global do_async
    logger.info("setting flags to {}".format(flags))
    if "test_async" in flags and flags["test_async"]:
        do_async = True


def get_capabilities():
    return {
        "flags": {
            "supports_async": True,
            "security_messages": True,
            "new_message_format": True,
            "connect_v2": True,
            "network_disconnect": True,
            "connection_status": True,
        },
        "skip_list": ["invokesModuleMethodCalls", "invokesDeviceMethodCalls"],
    }


def run_shell_command(args):
    logger.info("running [{}]".format(" ".join(args)))
    try:
        return subprocess.check_output(args).decode("utf-8").splitlines()
    except subprocess.CalledProcessError as e:
        logger.error("Error spawning {}".format(e.cmd))
        logger.error("Process returned {}".format(e.returncode))
        logger.error("process output: {}".format(e.output))
        raise


def disconnect_port(disconnect_type, port):
    # sudo -n iptables -A OUTPUT -p tcp --dport 8883 -j DROP
    run_shell_command(
        [
            "sudo",
            "-n",
            "iptables",
            "-A",
            "OUTPUT",
            "-p",
            "tcp",
            "--dport",
            str(port),
            "-j",
            disconnect_type,
        ]
    )


def reconnect_port(port):
    for disconnect_type in all_disconnect_types:
        # sudo -n iptables -L OUTPUT -n -v --line-numbers
        lines = run_shell_command(
            ["sudo", "-n", "iptables", "-L", "OUTPUT", "-n", "-v", "--line-numbers"]
        )
        # do the lines in reverse because deleting an entry changes the line numbers of all entries after that.
        lines.reverse()
        for line in lines:
            if disconnect_type in line and str(port) in line:
                line_number = line.split(" ")[0]
                logger.info("Removing {} from [{}]".format(line_number, line))
                # sudo -n iptables -D OUTPUT 1
                run_shell_command(
                    ["sudo", "-n", "iptables", "-D", "OUTPUT", str(line_number)]
                )


def network_disconnect(disconnect_type):
    if disconnect_type not in all_disconnect_types:
        raise ValueError(
            "disconnect_type {} invalid.  Only DROP and REJECT are accepted".format(
                disconnect_type
            )
        )
    disconnect_port(disconnect_type, mqtt_port)


def network_reconnect():
    reconnect_port(mqtt_port)
