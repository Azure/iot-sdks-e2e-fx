import connexion
import six

from swagger_server import util


def wrapper_cleanup():  # noqa: E501
    """verify that the clients have cleaned themselves up completely

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def wrapper_get_capabilities():  # noqa: E501
    """Get capabilities for this test wrapper

     # noqa: E501


    :rtype: object
    """
    return 'do some magic!'


def wrapper_log_message(msg):  # noqa: E501
    """log a message to output

     # noqa: E501

    :param msg: 
    :type msg: 

    :rtype: None
    """
    return 'do some magic!'


def wrapper_network_disconnect(disconnectionType):  # noqa: E501
    """simulate a network disconnection

     # noqa: E501

    :param disconnectionType: 
    :type disconnectionType: str

    :rtype: None
    """
    return 'do some magic!'


def wrapper_network_reconnect():  # noqa: E501
    """Reconnect the network after a simulated network disconnection

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def wrapper_set_flags(flags):  # noqa: E501
    """set flags for the wrapper to use

     # noqa: E501

    :param flags: 
    :type flags: 

    :rtype: None
    """
    return 'do some magic!'
