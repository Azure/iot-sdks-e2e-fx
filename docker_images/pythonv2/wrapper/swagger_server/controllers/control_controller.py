import connexion
import six

from swagger_server.models.log_message import LogMessage  # noqa: E501
from swagger_server import util
# added 1 line in merge
import control_glue


def control_cleanup():  # noqa: E501
    """verify that the clients have cleaned themselves up completely

     # noqa: E501


    :rtype: None
    """
    # changed from return 'do some magic!'
    control_glue.cleanup_resources()


def control_get_capabilities():  # noqa: E501
    """Get capabilities for the objects in this server

     # noqa: E501


    :rtype: object
    """
    # changed from return 'do some magic!'
    return control_glue.get_capabilities()


def control_log_message(logMessage):  # noqa: E501
    """log a message to output

     # noqa: E501

    :param logMessage: 
    :type logMessage: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        logMessage = LogMessage.from_dict(connexion.request.get_json())  # noqa: E501
    # changed from return 'do some magic!'
    control_glue.log_message(logMessage.message)


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
    # changed from return 'do some magic!'
    control_glue.set_flags(flags)

