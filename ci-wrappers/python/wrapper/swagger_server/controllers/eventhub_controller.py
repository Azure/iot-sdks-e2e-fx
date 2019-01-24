import connexion
import six

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server import util


def eventhub_connect_put(connectionString):  # noqa: E501
    """Connect to eventhub

    Connect to the Azure eventhub service. # noqa: E501

    :param connectionString: Service connection string
    :type connectionString: str

    :rtype: ConnectResponse
    """
    return 'do some magic!'


def eventhub_connection_id_device_telemetry_device_id_get(connectionId, deviceId):  # noqa: E501
    """wait for telemetry sent from a specific device

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str

    :rtype: str
    """
    return 'do some magic!'


def eventhub_connection_id_disconnect_put(connectionId):  # noqa: E501
    """Disconnect from the eventhub

    Disconnects from the Azure eventhub service # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def eventhub_connection_id_enable_telemetry_put(connectionId):  # noqa: E501
    """Enable telemetry

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'
