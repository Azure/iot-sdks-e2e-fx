# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import subprocess

logger = logging.getLogger("droopy." + __name__)

mqtt_port = 8883
mqttws_port = 443
uninitialized = "uninitialized"
sudo_prefix = uninitialized
all_disconnect_types = ["DROP", "REJECT"]
all_transports = ["mqtt", "mqttws"]


def get_sudo_prefix():
    global sudo_prefix

    # use "uninitialized" to mean uninitialized, because None and [] are both falsy and we want to set it to [], so we can't use None
    if sudo_prefix == uninitialized:
        try:
            run_shell_command("which sudo")
        except subprocess.CalledProcessError:
            sudo_prefix = ""
        else:
            sudo_prefix = "sudo -n "

    return sudo_prefix


def run_shell_command(cmd):
    logger.info("running [{}]".format(cmd))
    try:
        return subprocess.check_output(cmd.split(" ")).decode("utf-8").splitlines()
    except subprocess.CalledProcessError as e:
        logger.error("Error spawning {}".format(e.cmd))
        logger.error("Process returned {}".format(e.returncode))
        logger.error("process output: {}".format(e.output))
        raise


def transport_to_port(transport):
    if transport == "mqtt":
        return mqtt_port
    elif transport == "mqttws":
        return mqttws_port
    else:
        raise ValueError(
            "transport_type {} invalid.  Only mqtt and mqttws are accepted".format(
                transport
            )
        )


def disconnect_port(disconnect_type, transport):
    # sudo -n iptables -A OUTPUT -p tcp --dport 8883 -j DROP
    port = transport_to_port(transport)
    run_shell_command(
        "{}iptables -A OUTPUT -p tcp --dport {} -j {}".format(
            get_sudo_prefix(), port, disconnect_type
        )
    )


def reconnect_port(transport):
    port = transport_to_port(transport)
    for disconnect_type in all_disconnect_types:
        # sudo -n iptables -L OUTPUT -n -v --line-numbers
        lines = run_shell_command(
            "{}iptables -L OUTPUT -n -v --line-numbers".format(get_sudo_prefix())
        )
        # do the lines in reverse because deleting an entry changes the line numbers of all entries after that.
        lines.reverse()
        for line in lines:
            if disconnect_type in line and str(port) in line:
                line_number = line.split(" ")[0]
                logger.info("Removing {} from [{}]".format(line_number, line))
                # sudo -n iptables -D OUTPUT 1
                run_shell_command(
                    "{}iptables -D OUTPUT {}".format(get_sudo_prefix(), line_number)
                )
