// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using IO.Swagger.Models;
using Microsoft.Azure.Devices;
using Microsoft.Azure.Devices.Client;
using Newtonsoft.Json;
using System;
using System.Text;

#pragma warning disable CA1304, CA1305, CA1307 // string function could vary with locale

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// Object which glues the swagger generated wrappers to the various IoTHub SDKs
    /// </summary>
    internal class GlueUtils
    {
        private GlueUtils()
        {
        }

        internal static IotHubClientOptions TransportNameToOptions(string transport)
        {
            switch (transport.ToLower())
            {
                case "mqtt":
                    return new IotHubClientOptions(new IotHubClientMqttSettings());
                case "mqttws":
                    return new IotHubClientOptions(new IotHubClientMqttSettings(IotHubClientTransportProtocol.WebSocket));
                case "amqp":
                    return new IotHubClientOptions(new IotHubClientAmqpSettings());
                case "amqpws":
                    return new IotHubClientOptions(new IotHubClientAmqpSettings(IotHubClientTransportProtocol.WebSocket));
                default:
                    throw new ArgumentException("unknown transport " + transport);
            }
        }

        internal static DirectMethodServiceRequest CreateDirectMethodServiceRequest(MethodInvoke methodInvokeParameters)
        {
            var method = new DirectMethodServiceRequest(methodInvokeParameters.MethodName)
            {
                // PayloadAsObject serializes the value to JSON bytes via
                // Newtonsoft and stores them in the wire-level Payload byte[].
                PayloadAsObject = methodInvokeParameters.Payload,
            };
            if (methodInvokeParameters.ResponseTimeoutInSeconds.HasValue)
            {
                method.ResponseTimeout = TimeSpan.FromSeconds(methodInvokeParameters.ResponseTimeoutInSeconds.Value);
            }
            if (methodInvokeParameters.ConnectTimeoutInSeconds.HasValue)
            {
                method.ConnectionTimeout = TimeSpan.FromSeconds(methodInvokeParameters.ConnectTimeoutInSeconds.Value);
            }
            return method;
        }

        internal static byte[] ObjectToBytes(object obj)
        {
            return Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(obj));
        }

        internal static EdgeModuleDirectMethodRequest CreateEdgeModuleDirectMethodRequest(MethodInvoke methodInvokeParameters)
        {
            var request = new EdgeModuleDirectMethodRequest(methodInvokeParameters.MethodName, GlueUtils.ObjectToBytes(methodInvokeParameters.Payload));
            if (methodInvokeParameters.ResponseTimeoutInSeconds.HasValue)
            {
                request.ResponseTimeout = TimeSpan.FromSeconds(methodInvokeParameters.ResponseTimeoutInSeconds.Value);
            }
            if (methodInvokeParameters.ConnectTimeoutInSeconds.HasValue)
            {
                request.ConnectionTimeout = TimeSpan.FromSeconds(methodInvokeParameters.ConnectTimeoutInSeconds.Value);
            }
            return request;
        }
    }
}
