// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using IO.Swagger.Models;
using Microsoft.Azure.Devices;
using Microsoft.Azure.Devices.Client;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
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

        internal static byte[] ObjectToBytes(object obj)
        {
            return Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(obj));
        }

        // Convert a payload byte[] (UTF-8 of a JSON value) returned by the SDK
        // into a JToken to embed in a wrapper response. Falls back to a JSON
        // string if the bytes are not valid JSON.
        internal static JToken PayloadBytesToJson(byte[] bytes)
        {
            if (bytes == null || bytes.Length == 0)
            {
                return null;
            }
            string text = Encoding.UTF8.GetString(bytes);
            try
            {
                return JToken.Parse(text);
            }
            catch (JsonException)
            {
                return new JValue(text);
            }
        }

        internal static EdgeModuleDirectMethodRequest CreateEdgeModuleDirectMethodRequest(MethodInvoke methodInvokeParameters)
        {
            var request = new EdgeModuleDirectMethodRequest(methodInvokeParameters.MethodName, GlueUtils.ObjectToBytes(methodInvokeParameters.Payload));
            if (methodInvokeParameters.ResponseTimeoutInSeconds.HasValue)
            {
#if SDK_NET10
                request.ResponseTimeoutInSeconds = (int)methodInvokeParameters.ResponseTimeoutInSeconds.Value;
#else
                request.ResponseTimeout = TimeSpan.FromSeconds(methodInvokeParameters.ResponseTimeoutInSeconds.Value);
#endif
            }
            if (methodInvokeParameters.ConnectTimeoutInSeconds.HasValue)
            {
#if SDK_NET10
                request.ConnectTimeoutInSeconds = (int)methodInvokeParameters.ConnectTimeoutInSeconds.Value;
#else
                request.ConnectionTimeout = TimeSpan.FromSeconds(methodInvokeParameters.ConnectTimeoutInSeconds.Value);
#endif
            }
            return request;
        }

#if SDK_NET10
        /// <summary>
        /// Convert a PropertyCollection to a JObject that Newtonsoft.Json can
        /// serialize natively.  PropertyCollection may contain types that
        /// Newtonsoft does not serialize correctly when boxed inside a
        /// Dictionary&lt;string,object&gt;.  Roundtripping through Newtonsoft's
        /// own serializer and JObject.Parse produces a clean JObject tree.
        /// </summary>
        internal static JObject PropertyCollectionToJObject(PropertyCollection pc)
        {
            // Log types for diagnostics
            foreach (var kv in pc)
            {
                Console.WriteLine("PropertyCollection[{0}] type={1} value={2}",
                    kv.Key, kv.Value?.GetType().FullName ?? "null", kv.Value);
            }

            // Serialize via Newtonsoft (which knows all its own types) then
            // re-parse into a JObject.
            string json = JsonConvert.SerializeObject(pc);
            Console.WriteLine("PropertyCollection JSON via Newtonsoft: " + json);
            var jobj = JObject.Parse(json);
            // Ensure $version is included
            if (!jobj.ContainsKey("$version"))
            {
                jobj["$version"] = pc.Version;
            }
            return jobj;
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
                return System.Text.Json.JsonSerializer.Deserialize<object>(bytes);
            }
            catch
            {
                return Encoding.UTF8.GetString(bytes);
            }
        }

        private static object ToNativeValue(object value)
        {
            if (value == null) return null;
            // Handle Newtonsoft JToken types BEFORE the IEnumerable check.
            // JToken implements IEnumerable<JToken>, so a JValue("some string")
            // would match IEnumerable<object> and produce [] (empty array)
            // because JValue yields zero children when enumerated.
            if (value is JToken jt) return JTokenToNative(jt);
            if (value is string || value is int || value is long || value is double || value is bool) return value;
            if (value is DateTimeOffset dto) return dto.ToString("o");
            if (value is IDictionary<string, object> dict)
            {
                return dict.ToDictionary(kv => kv.Key, kv => ToNativeValue(kv.Value));
            }
            if (value is IEnumerable<object> list)
            {
                return list.Select(ToNativeValue).ToList();
            }
            return value;
        }

        private static object JTokenToNative(JToken token)
        {
            switch (token.Type)
            {
                case JTokenType.Object:
                    return ((JObject)token).Properties()
                        .ToDictionary(p => p.Name, p => JTokenToNative(p.Value));
                case JTokenType.Array:
                    return ((JArray)token).Select(JTokenToNative).ToList();
                case JTokenType.Integer:
                    return token.Value<long>();
                case JTokenType.Float:
                    return token.Value<double>();
                case JTokenType.String:
                    return token.Value<string>();
                case JTokenType.Boolean:
                    return token.Value<bool>();
                case JTokenType.Null:
                case JTokenType.Undefined:
                    return null;
                case JTokenType.Date:
                    return token.Value<DateTimeOffset>().ToString("o");
                default:
                    return token.ToString();
            }
        }
#endif
    }
}
