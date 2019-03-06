import docker
import sys
import os
from adapters import print_message as log_message
from time import sleep

# Create Global Variables
EDGEHUB_NAME = "edgeHub"
client = docker.from_env()
try:
    edge_network = client.networks.get("azure-iot-edge")
    edgeHub = client.containers.get(EDGEHUB_NAME)
except:
    print("Could not load docker engine.")
    edge_network = None
    edgeHub = None


def get_network_list():
    edge_network.reload()
    return list(map(lambda x: x.name, edge_network.containers))


def disconnect_edgehub(network=True):
    log_message("disconnecting edgehub from network")
    try:
        edgeHub = client.containers.get(EDGEHUB_NAME)
        if network:
            if EDGEHUB_NAME in get_network_list():
                edge_network.disconnect(EDGEHUB_NAME)
                sleep(10)
            else:  # Edge Network alreday contains EdgeHub
                log_message("Note: {} not in IoT Edge Network".format(EDGEHUB_NAME))
        else:
            if EDGEHUB_NAME in list(map(lambda x: x.name, client.containers.list())):
                edgeHub.restart()
            else:  # Edge Network alreday contains EdgeHub
                log_message("Note: {} not in IoT Edge Network".format(EDGEHUB_NAME))
    except Exception as e:
        log_message("Error: {}".format(sys.exc_info()[0]))
        raise e


def connect_edgehub(network=True):
    log_message("connecting edgehub to network")
    try:
        log_message(" edgeHub = client.containers.get(EDGEHUB_NAME)")
        edgeHub = client.containers.get(EDGEHUB_NAME)
        if network:
            if EDGEHUB_NAME not in get_network_list():
                log_message("edge_network.connect(EDGEHUB_NAME)")
                edge_network.connect(EDGEHUB_NAME)
            else:  # Edge Network alreday contains EdgeHub
                log_message("Note: {} already in IoT Edge Network".format(EDGEHUB_NAME))
        else:
            log_message("network=False")
            while edgeHub.status != "running":
                log_message("edgehub not running")
                edgeHub.start()
                log_message("Waiting for edgeHub to come back online...")
                sleep(1)
                edgeHub = client.containers.get(EDGEHUB_NAME)
            log_message("EXITED WHILE LOOP")
            if edgeHub.status == "running":
                log_message(
                    "~~~~~~~~~~~~~~~~~~edgeHub started~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
                )
                log_message("sleeping...")
                sleep(5)
                log_message("done sleeping!")
    except Exception as e:
        log_message(
            "THIS IS AN EXCEPTION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        )
        log_message("Error: {}".format(sys.exc_info()[0]))
        raise e


def restart_edgehub(hard=False):
    log_message("restarting edgehub")
    client = docker.from_env()
    edgeHub = client.containers.get(EDGEHUB_NAME)
    try:
        if hard:            client = docker.from_env()
            containerList = []
            for i in client.containers.list():
                if "Mod" or "edgeHub" in i.name:
                    name = client.containers.get(name)
                    list.append(name)
            for i in containerList:
                i.restart()
            while EDGEHUB_NAME not in list(
                map(lambda x: x.name, client.containers.list())
            ):
                log_message("waiting for edge daemon to revive edgehub...")
                sleep(1)
            log_message("updating pointer to edgehub container")
            edgeHub.reload()
        else:
            edgeHub.restart()
            sleep(5)
    except Exception as e:
        log_message("Error: {}".format(sys.exc_info()[0]))
        raise e
