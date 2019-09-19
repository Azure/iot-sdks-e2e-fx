import connexion
import six

from swagger_server import util
# added 1 line in merge
import wrapper_glue


def wrapper_cleanup():  # noqa: E501
    """verify that the clients have cleaned themselves up completely

     # noqa: E501


    :rtype: None
    """
    # changed from return 'do some magic!'
    wrapper_glue.cleanup_resources()


def wrapper_get_capabilities():  # noqa: E501
    """Get capabilities for this test wrapper

     # noqa: E501


    :rtype: object
    """
    # changed from return 'do some magic!'
    return wrapper_glue.get_capabilities()


def wrapper_log_message(msg):  # noqa: E501
    """log a message to output

     # noqa: E501

    :param msg: 
    :type msg: 

    :rtype: None
    """
    # changed from return 'do some magic!'
    wrapper_glue.log_message(msg)

def wrapper_network_disconnect(disconnectionType):  # noqa: E501
    """simulate a network disconnection

     # noqa: E501

    :param disconnectionType: 
    :type disconnectionType: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    wrapper_glue.network_disconnect(disconnectionType)


def wrapper_network_reconnect():  # noqa: E501
    """Reconnect the network after a simulated network disconnection

     # noqa: E501


    :rtype: None
    """
    # changed from return 'do some magic!'
    wrapper_glue.network_reconnect()


def wrapper_set_flags(flags):  # noqa: E501
    """set flags for the wrapper to use

     # noqa: E501

    :param flags: 
    :type flags: 

    :rtype: None
    """
    # changed from return 'do some magic!'
    wrapper_glue.set_flags(flags)

