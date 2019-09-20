import connexion
import six

from swagger_server import util
from swagger_server import wrapper_glue

def wrapper_cleanup_put():  # noqa: E501
    """verify that the clients have cleaned themselves up completely

     # noqa: E501


    :rtype: None
    """
    wrapper_glue.cleanup_resources()


def wrapper_configuration_get():  # noqa: E501
    """gets configuration details on the current wrapper configuration

     # noqa: E501


    :rtype: object
    """
    return 'do some magic!'


def wrapper_message_put(msg):  # noqa: E501
    """log a message to output

     # noqa: E501

    :param msg:
    :type msg:

    :rtype: None
    """
    wrapper_glue.log_message(msg)



def wrapper_session_get():  # noqa: E501
    """Terminate a wrapper, optionally returning the log

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'


def wrapper_session_put():  # noqa: E501
    """Launch a wrapper, getting ready to test

     # noqa: E501


    :rtype: None
    """
    return 'do some magic!'
