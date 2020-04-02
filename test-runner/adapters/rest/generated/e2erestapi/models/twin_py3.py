# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class Twin(Model):
    """device twin or module twin.

    :param desired: desired properties
    :type desired: object
    :param reported: reported properties
    :type reported: object
    """

    _attribute_map = {
        'desired': {'key': 'desired', 'type': 'object'},
        'reported': {'key': 'reported', 'type': 'object'},
    }

    def __init__(self, *, desired=None, reported=None, **kwargs) -> None:
        super(Twin, self).__init__(**kwargs)
        self.desired = desired
        self.reported = reported
