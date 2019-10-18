# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import subprocess

logger = logging.getLogger(__name__)

do_async = False

all_disconnect_types = ["DROP", "REJECT"]
mqtt_port = 8883
mqttws_port = 443
uninitialized = "uninitialized"
sudo_prefix = uninitialized


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
            "v2_connect_group": True,
            "dropped_connection_tests": True,
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


def get_sudo_prefix():
    global sudo_prefix

    # use "uninitialized" to mean uninitialized, because None and [] are both falsy and we want to set it to [], so we can't use None
    if sudo_prefix == uninitialized:
        try:
            run_shell_command(["which", "sudo"])
        except subprocess.CalledProcessError:
            sudo_prefix = []
        else:
            sudo_prefix = ["sudo", "-n"]

    return sudo_prefix


def disconnect_port(disconnect_type, port):
    # sudo -n iptables -A OUTPUT -p tcp --dport 8883 -j DROP
    run_shell_command(
        get_sudo_prefix()
        + [
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
            get_sudo_prefix()
            + ["iptables", "-L", "OUTPUT", "-n", "-v", "--line-numbers"]
        )
        # do the lines in reverse because deleting an entry changes the line numbers of all entries after that.
        lines.reverse()
        for line in lines:
            if disconnect_type in line and str(port) in line:
                line_number = line.split(" ")[0]
                logger.info("Removing {} from [{}]".format(line_number, line))
                # sudo -n iptables -D OUTPUT 1
                run_shell_command(
                    get_sudo_prefix() + ["iptables", "-D", "OUTPUT", str(line_number)]
                )


def network_disconnect(transport, disconnect_type):
    if disconnect_type not in all_disconnect_types:
        raise ValueError(
            "disconnect_type {} invalid.  Only DROP and REJECT are accepted".format(
                disconnect_type
            )
        )

    if transport == "mqtt":
        disconnect_port(disconnect_type, mqtt_port)
    elif transport == "mqttws":
        disconnect_port(disconnect_type, mqttws_port)
    else:
        raise ValueError(
            "transport_type {} invalid.  Only mqtt and mqttws are accepted".format(
                transport
            )
        )


def network_reconnect():
    reconnect_port(mqtt_port)
    reconnect_port(mqttws_port)
