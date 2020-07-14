import connexion
import six

from swagger_server.models.log_message import LogMessage  # noqa: E501
from swagger_server import util


def control_cleanup():  # noqa: E501
    """verify that the clients have cleaned themselves up completely

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def control_get_capabilities():  # noqa: E501
    """Get capabilities for the objects in this server

     # noqa: E501


    :rtype: object
    """
    return 'do some magic!'


def control_get_wrapper_stats():  # noqa: E501
    """Get statistics about the operation of the test wrapper

     # noqa: E501


    :rtype: object
    """
    return 'do some magic!'


def control_log_message(logMessage):  # noqa: E501
    """log a message to output

     # noqa: E501

    :param logMessage: 
    :type logMessage: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        logMessage = LogMessage.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def control_send_command(cmd):  # noqa: E501
    """send an arbitrary command

     # noqa: E501

    :param cmd: command string
    :type cmd: str

    :rtype: None
    """
    return 'do some magic!'


def control_set_flags(flags):  # noqa: E501
    """set flags for the objects in this server to use

     # noqa: E501

    :param flags: 
    :type flags: 

    :rtype: None
    """
    return 'do some magic!'
