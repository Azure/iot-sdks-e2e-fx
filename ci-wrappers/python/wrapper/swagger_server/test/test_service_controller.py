# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestServiceController(BaseTestCase):
    """ServiceController integration test stubs"""

    def test_service_connect_put(self):
        """Test case for service_connect_put

        Connect to service
        """
        query_string = [('connectionString', 'connectionString_example')]
        response = self.client.open(
            '/service/connect',
            method='PUT',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_service_connection_id_device_method_device_id_put(self):
        """Test case for service_connection_id_device_method_device_id_put

        call the given method on the given device
        """
        methodInvokeParameters = None
        response = self.client.open(
            '/service/{connectionId}/deviceMethod/{deviceId}'.format(connectionId='connectionId_example', deviceId='deviceId_example'),
            method='PUT',
            data=json.dumps(methodInvokeParameters),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_service_connection_id_disconnect_put(self):
        """Test case for service_connection_id_disconnect_put

        Disconnect from the service
        """
        response = self.client.open(
            '/service/{connectionId}/disconnect/'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_service_connection_id_module_method_device_id_module_id_put(self):
        """Test case for service_connection_id_module_method_device_id_module_id_put

        call the given method on the given module
        """
        methodInvokeParameters = None
        response = self.client.open(
            '/service/{connectionId}/moduleMethod/{deviceId}/{moduleId}'.format(connectionId='connectionId_example', deviceId='deviceId_example', moduleId='moduleId_example'),
            method='PUT',
            data=json.dumps(methodInvokeParameters),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
