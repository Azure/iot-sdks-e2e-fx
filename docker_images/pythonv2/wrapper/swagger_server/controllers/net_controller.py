import connexion
import six

from swagger_server import util


def net_disconnect(disconnectType):  # noqa: E501
    """Simulate a network disconnection

     # noqa: E501

    :param disconnectType: disconnect method for dropped connection tests
    :type disconnectType: str

    :rtype: None
    """
    return 'do some magic!'


def net_disconnect_after_c2d(disconnectType):  # noqa: E501
    """Simulate a disconnect after the next C2D transfer

     # noqa: E501

    :param disconnectType: disconnect method for dropped connection tests
    :type disconnectType: str

    :rtype: None
    """
    return 'do some magic!'


def net_disconnect_after_d2c(disconnectType):  # noqa: E501
    """Simulate a disconnect after the next D2C transfer

     # noqa: E501

    :param disconnectType: disconnect method for dropped connection tests
    :type disconnectType: str

    :rtype: None
    """
    return 'do some magic!'


def net_reconnect():  # noqa: E501
    """Reconnect the network after a simulated network disconnection

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def net_set_destination(ip, transportType):  # noqa: E501
    """Set destination for net disconnect ops

     # noqa: E501

    :param ip: 
    :type ip: str
    :param transportType: Transport to use
    :type transportType: str

    :rtype: None
    """
    return 'do some magic!'
