# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.method_request_response import MethodRequestResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestDeviceController(BaseTestCase):
    """DeviceController integration test stubs"""

    def test_device_connect_transport_type_put(self):
        """Test case for device_connect_transport_type_put

        Connect to the azure IoT Hub as a device
        """
        caCertificate = Certificate()
        query_string = [('connectionString', 'connectionString_example')]
        response = self.client.open(
            '/device/connect/{transportType}'.format(transportType='transportType_example'),
            method='PUT',
            data=json.dumps(caCertificate),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_device_connection_id_disconnect_put(self):
        """Test case for device_connection_id_disconnect_put

        Disconnect the device
        """
        response = self.client.open(
            '/device/{connectionId}/disconnect'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_device_connection_id_enable_methods_put(self):
        """Test case for device_connection_id_enable_methods_put

        Enable methods
        """
        response = self.client.open(
            '/device/{connectionId}/enableMethods'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_device_connection_id_method_request_method_name_get(self):
        """Test case for device_connection_id_method_request_method_name_get

        Wait for a method call with the given name
        """
        response = self.client.open(
            '/device/{connectionId}/methodRequest/{methodName}'.format(connectionId='connectionId_example', methodName='methodName_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_device_connection_id_method_response_response_id_status_code_put(self):
        """Test case for device_connection_id_method_response_response_id_status_code_put

        Respond to the method call with the given name
        """
        responseBody = None
        response = self.client.open(
            '/device/{connectionId}/methodResponse/{responseId}/{statusCode}'.format(connectionId='connectionId_example', responseId='responseId_example', statusCode='statusCode_example'),
            method='PUT',
            data=json.dumps(responseBody),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
