# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.test import BaseTestCase


class TestWrapperController(BaseTestCase):
    """WrapperController integration test stubs"""

    def test_wrapper_cleanup_put(self):
        """Test case for wrapper_cleanup_put

        verify that the clients have cleaned themselves up completely
        """
        response = self.client.open(
            '/wrapper/cleanup',
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_wrapper_configuration_get(self):
        """Test case for wrapper_configuration_get

        gets configuration details on the current wrapper configuration
        """
        response = self.client.open(
            '/wrapper/configuration',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_wrapper_message_put(self):
        """Test case for wrapper_message_put

        log a message to output
        """
        msg = None
        response = self.client.open(
            '/wrapper/message',
            method='PUT',
            data=json.dumps(msg),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_wrapper_session_get(self):
        """Test case for wrapper_session_get

        Terminate a wrapper, optionally returning the log
        """
        response = self.client.open(
            '/wrapper/session',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_wrapper_session_put(self):
        """Test case for wrapper_session_put

        Launch a wrapper, getting ready to test
        """
        response = self.client.open(
            '/wrapper/session',
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
