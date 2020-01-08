# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class EventBody(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, body=None, horton_flags=None, attributes=None):  # noqa: E501
        """EventBody - a model defined in Swagger

        :param body: The body of this EventBody.  # noqa: E501
        :type body: object
        :param horton_flags: The horton_flags of this EventBody.  # noqa: E501
        :type horton_flags: object
        :param attributes: The attributes of this EventBody.  # noqa: E501
        :type attributes: object
        """
        self.swagger_types = {
            'body': object,
            'horton_flags': object,
            'attributes': object
        }

        self.attribute_map = {
            'body': 'body',
            'horton_flags': 'horton_flags',
            'attributes': 'attributes'
        }

        self._body = body
        self._horton_flags = horton_flags
        self._attributes = attributes

    @classmethod
    def from_dict(cls, dikt):
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The eventBody of this EventBody.  # noqa: E501
        :rtype: EventBody
        """
        return util.deserialize_model(dikt, cls)

    @property
    def body(self):
        """Gets the body of this EventBody.

        payload to send to the method  # noqa: E501

        :return: The body of this EventBody.
        :rtype: object
        """
        return self._body

    @body.setter
    def body(self, body):
        """Sets the body of this EventBody.

        payload to send to the method  # noqa: E501

        :param body: The body of this EventBody.
        :type body: object
        """

        self._body = body

    @property
    def horton_flags(self):
        """Gets the horton_flags of this EventBody.

        flags used by horton  # noqa: E501

        :return: The horton_flags of this EventBody.
        :rtype: object
        """
        return self._horton_flags

    @horton_flags.setter
    def horton_flags(self, horton_flags):
        """Sets the horton_flags of this EventBody.

        flags used by horton  # noqa: E501

        :param horton_flags: The horton_flags of this EventBody.
        :type horton_flags: object
        """

        self._horton_flags = horton_flags

    @property
    def attributes(self):
        """Gets the attributes of this EventBody.

        Message attributes  # noqa: E501

        :return: The attributes of this EventBody.
        :rtype: object
        """
        return self._attributes

    @attributes.setter
    def attributes(self, attributes):
        """Sets the attributes of this EventBody.

        Message attributes  # noqa: E501

        :param attributes: The attributes of this EventBody.
        :type attributes: object
        """

        self._attributes = attributes
