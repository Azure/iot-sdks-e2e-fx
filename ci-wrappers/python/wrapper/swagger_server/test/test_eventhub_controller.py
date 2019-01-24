# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestEventhubController(BaseTestCase):
    """EventhubController integration test stubs"""

    def test_eventhub_connect_put(self):
        """Test case for eventhub_connect_put

        Connect to eventhub
        """
        query_string = [('connectionString', 'connectionString_example')]
        response = self.client.open(
            '/eventhub/connect',
            method='PUT',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_eventhub_connection_id_device_telemetry_device_id_get(self):
        """Test case for eventhub_connection_id_device_telemetry_device_id_get

        wait for telemetry sent from a specific device
        """
        response = self.client.open(
            '/eventhub/{connectionId}/deviceTelemetry/{deviceId}'.format(connectionId='connectionId_example', deviceId='deviceId_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_eventhub_connection_id_disconnect_put(self):
        """Test case for eventhub_connection_id_disconnect_put

        Disconnect from the eventhub
        """
        response = self.client.open(
            '/eventhub/{connectionId}/disconnect/'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_eventhub_connection_id_enable_telemetry_put(self):
        """Test case for eventhub_connection_id_enable_telemetry_put

        Enable telemetry
        """
        response = self.client.open(
            '/eventhub/{connectionId}/enableTelemetry'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
