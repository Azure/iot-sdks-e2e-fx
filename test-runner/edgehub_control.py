import docker
import sys
import os
from adapters import adapter_config
from time import sleep

# Create Global Variables
EDGEHUB_NAME = "edgeHub"
client = docker.from_env()
try:
    edge_network = client.networks.get("azure-iot-edge")
    edgeHub = client.containers.get(EDGEHUB_NAME)
except:  # noqa: E722 do not use bare 'except'
    print("Could not load docker engine.")
    edge_network = None
    edgeHub = None


def get_network_list():
    edge_network.reload()
    return list(map(lambda x: x.name, edge_network.containers))


def disconnect_edgehub(network=True):
    adapter_config.logger("disconnecting edgehub from network")
    try:
        edgeHub = client.containers.get(EDGEHUB_NAME)
        if network:
            if EDGEHUB_NAME in get_network_list():
                edge_network.disconnect(EDGEHUB_NAME)
                sleep(10)
            else:  # Edge Network alreday contains EdgeHub
                adapter_config.logger(
                    "Note: {} not in IoT Edge Network".format(EDGEHUB_NAME)
                )
        else:
            if EDGEHUB_NAME in list(map(lambda x: x.name, client.containers.list())):
                edgeHub.restart()
            else:  # Edge Network alreday contains EdgeHub
                adapter_config.logger(
                    "Note: {} not in IoT Edge Network".format(EDGEHUB_NAME)
                )
    except Exception as e:
        adapter_config.logger("Error: {}".format(sys.exc_info()[0]))
        raise e


def connect_edgehub(network=True):
    adapter_config.logger("connecting edgehub to network")
    try:
        adapter_config.logger(" edgeHub = client.containers.get(EDGEHUB_NAME)")
        edgeHub = client.containers.get(EDGEHUB_NAME)
        if network:
            if EDGEHUB_NAME not in get_network_list():
                adapter_config.logger("edge_network.connect(EDGEHUB_NAME)")
                edge_network.connect(EDGEHUB_NAME)
            else:  # Edge Network alreday contains EdgeHub
                adapter_config.logger(
                    "Note: {} already in IoT Edge Network".format(EDGEHUB_NAME)
                )
        else:
            adapter_config.logger("network=False")
            while edgeHub.status != "running":
                adapter_config.logger("edgehub not running")
                edgeHub.start()
                adapter_config.logger("Waiting for edgeHub to come back online...")
                sleep(1)
                edgeHub = client.containers.get(EDGEHUB_NAME)
            adapter_config.logger("EXITED WHILE LOOP")
            if edgeHub.status == "running":
                adapter_config.logger(
                    "~~~~~~~~~~~~~~~~~~edgeHub started~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
                )
                adapter_config.logger("sleeping...")
                sleep(5)
                adapter_config.logger("done sleeping!")
    except Exception as e:
        adapter_config.logger(
            "THIS IS AN EXCEPTION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        )
        adapter_config.logger("Error: {}".format(sys.exc_info()[0]))
        raise e


def restart_edgehub(hard=False):
    adapter_config.logger("restarting edgehub")
    sleep(5)
    client = docker.from_env()
    edgeHub = client.containers.get(EDGEHUB_NAME)
    try:
        if hard:
            client = docker.from_env()
            containerList = list(map(lambda x: x.name, client.containers.list()))

            for containerName in containerList:
                if "Mod" or "edgeHub" in containerName:
                    currentContainer = client.containers.get(containerName)
                    currentContainer.restart()
            while EDGEHUB_NAME not in list(
                map(lambda x: x.name, client.containers.list())
            ):
                print("waiting for edge daemon to revive edgehub...")
                sleep(1)
            print("updating pointer to edgehub container")
            edgeHub.reload()
        else:
            edgeHub.restart()
            sleep(5)
    except Exception as e:
        adapter_config.logger("Error: {}".format(sys.exc_info()[0]))
        raise e
