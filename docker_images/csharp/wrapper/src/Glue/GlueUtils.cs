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

        internal static Microsoft.Azure.Devices.Client.TransportType TransportNameToType(string transport)
        {
            switch (transport.ToLower())
            {
                case "mqtt":
                    return Microsoft.Azure.Devices.Client.TransportType.Mqtt_Tcp_Only;
                case "mqttws":
                    return Microsoft.Azure.Devices.Client.TransportType.Mqtt_WebSocket_Only;
                case "amqp":
                    return Microsoft.Azure.Devices.Client.TransportType.Amqp_Tcp_Only;
                case "amqpws":
                    return Microsoft.Azure.Devices.Client.TransportType.Amqp_WebSocket_Only;
                case "http":
                    return Microsoft.Azure.Devices.Client.TransportType.Http1;
                default:
                    throw new ArgumentException("unknown transport " + transport);
            }
        }

        internal static CloudToDeviceMethod CreateCloudToDeviceMethod(MethodInvoke methodInvokeParameters)
        {
            var method = new CloudToDeviceMethod(methodInvokeParameters.MethodName, TimeSpan.FromSeconds((double)methodInvokeParameters.ResponseTimeoutInSeconds), TimeSpan.FromSeconds((double)methodInvokeParameters.ConnectTimeoutInSeconds));
            method.SetPayloadJson(methodInvokeParameters.Payload.ToString());
            return method;
        }

        internal static byte[] ObjectToBytes(object obj)
        {
            return Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(obj));
        }

        internal static MethodRequest CreateMethodRequest(MethodInvoke methodInvokeParameters)
        {
            return new MethodRequest(methodInvokeParameters.MethodName, GlueUtils.ObjectToBytes(methodInvokeParameters.Payload), TimeSpan.FromSeconds((double)methodInvokeParameters.ResponseTimeoutInSeconds), TimeSpan.FromSeconds((double)methodInvokeParameters.ConnectTimeoutInSeconds));
        }


    }
}
