// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using IO.Swagger.Models;
using Microsoft.Azure.Devices;
using Microsoft.Azure.Devices.Client;
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Text;
using System.Text.Json;

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

        internal static byte[] ObjectToBytes(object obj)
        {
            return JsonSerializer.SerializeToUtf8Bytes(obj);
        }

        /// <summary>
        /// Convert a payload byte[] (UTF-8 JSON) returned by the SDK into a
        /// JsonElement for embedding in a wrapper response.
        /// </summary>
        internal static JsonElement? PayloadBytesToJsonElement(byte[] bytes)
        {
            if (bytes == null || bytes.Length == 0)
            {
                return null;
            }
            try
            {
                using var doc = JsonDocument.Parse(bytes);
                return doc.RootElement.Clone();
            }
            catch (JsonException)
            {
                // Not valid JSON — wrap as a JSON string.
                string text = Encoding.UTF8.GetString(bytes);
                using var doc = JsonDocument.Parse(JsonSerializer.Serialize(text));
                return doc.RootElement.Clone();
            }
        }

        internal static EdgeModuleDirectMethodRequest CreateEdgeModuleDirectMethodRequest(MethodInvoke methodInvokeParameters)
        {
            var request = new EdgeModuleDirectMethodRequest(methodInvokeParameters.MethodName, GlueUtils.ObjectToBytes(methodInvokeParameters.Payload));
            if (methodInvokeParameters.ResponseTimeoutInSeconds.HasValue)
            {
                request.ResponseTimeoutInSeconds = (int)methodInvokeParameters.ResponseTimeoutInSeconds.Value;
            }
            if (methodInvokeParameters.ConnectTimeoutInSeconds.HasValue)
            {
                request.ConnectTimeoutInSeconds = (int)methodInvokeParameters.ConnectTimeoutInSeconds.Value;
            }
            return request;
        }

        /// <summary>
        /// Convert a PropertyCollection to a Dictionary that STJ can serialize
        /// natively.
        ///
        /// PropertyCollection stores data in an internal
        /// IDictionary&lt;string,JsonElement&gt; via STJ's [JsonExtensionData].
        /// We read that dictionary directly via reflection and use
        /// JsonElement.Clone() to produce standalone values.
        /// </summary>
        internal static Dictionary<string, object> PropertyCollectionToDict(PropertyCollection pc)
        {
            var dict = new Dictionary<string, object>();

            PropertyInfo propsProperty = null;
            Type searchType = pc.GetType();
            while (searchType != null && propsProperty == null)
            {
                propsProperty = searchType.GetProperty("Properties",
                    BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly);
                if (propsProperty == null)
                    searchType = searchType.BaseType;
            }

            if (propsProperty != null)
            {
                var propsDict = propsProperty.GetValue(pc) as IDictionary<string, JsonElement>;
                if (propsDict != null)
                {
                    foreach (var kv in propsDict)
                    {
                        dict[kv.Key] = kv.Value.Clone();
                    }
                }
            }

            dict["$version"] = pc.Version;
            return dict;
        }

        /// <summary>
        /// Convert a payload byte[] (UTF-8 JSON) into a native .NET object
        /// that System.Text.Json can serialize correctly.
        /// </summary>
        internal static object PayloadBytesToNative(byte[] bytes)
        {
            if (bytes == null || bytes.Length == 0)
            {
                return null;
            }
            try
            {
                using var doc = JsonDocument.Parse(bytes);
                return doc.RootElement.Clone();
            }
            catch
            {
                return Encoding.UTF8.GetString(bytes);
            }
        }
    }
}
