import connexion
import six

from swagger_server import util
import wrapper_glue

def wrapper_cleanup():  # noqa: E501
    """verify that the clients have cleaned themselves up completely

     # noqa: E501


    :rtype: None
    """
    wrapper_glue.cleanup_resources()


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
    wrapper_glue.log_message(msg)

