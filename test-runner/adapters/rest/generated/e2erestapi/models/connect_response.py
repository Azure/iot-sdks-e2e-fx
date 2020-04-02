# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class ConnectResponse(Model):
    """result of a connection to a service, device, or module client.

    :param connection_id: unique identifier for this connection
    :type connection_id: str
    """

    _attribute_map = {
        'connection_id': {'key': 'connectionId', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(ConnectResponse, self).__init__(**kwargs)
        self.connection_id = kwargs.get('connection_id', None)
