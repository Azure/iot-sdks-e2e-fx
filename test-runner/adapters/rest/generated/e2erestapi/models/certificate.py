# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class Certificate(Model):
    """certificate in the body of a message.

    :param cert: unique identifier for this connection
    :type cert: str
    """

    _attribute_map = {
        'cert': {'key': 'cert', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(Certificate, self).__init__(**kwargs)
        self.cert = kwargs.get('cert', None)
