// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using IO.Swagger.Models;
using Microsoft.Azure.Devices;
using System.Diagnostics;
using System.Threading;

#pragma warning disable CA1304, CA1305, CA1307 // string function could vary with locale
#pragma warning disable CA1822 // method could be marked static
#pragma warning disable CA1822 // parameter is never used
#pragma warning disable CS1998 // async method lacks await operator

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// Object which glues the swagger generated wrappers to the various IoTHub SDKs
    /// </summary>
    internal class ServiceGlue
    {
        private static Dictionary<string, IotHubServiceClient> objectMap = new Dictionary<string, IotHubServiceClient>();
        // Stash the raw connection string so we can issue direct method calls
        // via the IoT Hub REST API. The v2 preview SDK's
        // DirectMethods.InvokeAsync serializes the payload byte[] as a JSON
        // base64 string (because DirectMethodServiceRequest.Payload is byte[]
        // with [JsonProperty("payload")]), which IoT Hub then forwards as a
        // string instead of a JSON object, causing the device-side handler to
        // see the wrong payload.
        private static Dictionary<string, string> connectionStringMap = new Dictionary<string, string>();
        private static readonly HttpClient s_httpClient = new HttpClient();
        private const string IotHubApiVersion = "2021-04-12";
        private static int objectCount = 0;
        private const string serviceClientPrefix = "serviceClient_";

        public ServiceGlue()
        {
        }

        public async Task<ConnectResponse> ConnectAsync(string connectionString)
        {
            var client = new IotHubServiceClient(connectionString);
            var connectionId = serviceClientPrefix + Convert.ToString(++objectCount);
            objectMap[connectionId] = client;
            connectionStringMap[connectionId] = connectionString;
            return new ConnectResponse
            {
                ConnectionId = connectionId
            };
        }

        public async Task DisconnectAsync(string connectionId)
        {
            if (objectMap.ContainsKey(connectionId))
            {
                var client = objectMap[connectionId];
                objectMap.Remove(connectionId);
                connectionStringMap.Remove(connectionId);
                client.Dispose();
            }
        }

        public async Task<object> InvokeModuleMethodAsync(string connectionId, string deviceId, string moduleId, MethodInvoke methodInvokeParameters)
        {
            Debug.WriteLine("InvokeModuleMethodAsync received for {0} with deviceId {1} and moduleId {2}", connectionId, deviceId, moduleId);
            Debug.WriteLine(methodInvokeParameters.ToString());
            var relativeUri = $"/twins/{Uri.EscapeDataString(deviceId)}/modules/{Uri.EscapeDataString(moduleId)}/methods";
            return await InvokeMethodViaRestAsync(connectionId, relativeUri, methodInvokeParameters).ConfigureAwait(false);
        }

        public async Task<object> InvokeDeviceMethodAsync(string connectionId, string deviceId, MethodInvoke methodInvokeParameters)
        {
            Debug.WriteLine("InvokeDeviceMethodAsync received for {0} with deviceId {1} ", connectionId, deviceId);
            Debug.WriteLine(methodInvokeParameters.ToString());
            var relativeUri = $"/twins/{Uri.EscapeDataString(deviceId)}/methods";
            return await InvokeMethodViaRestAsync(connectionId, relativeUri, methodInvokeParameters).ConfigureAwait(false);
        }

        // Workaround for v2 preview SDK bug: invoke direct methods via the IoT
        // Hub REST API directly so the payload travels as a real JSON value.
        private async Task<object> InvokeMethodViaRestAsync(string connectionId, string relativeUri, MethodInvoke methodInvokeParameters)
        {
            var connStr = connectionStringMap[connectionId];
            var (hostName, keyName, key) = ParseConnectionString(connStr);

            var bodyDict = new Dictionary<string, object>
            {
                ["methodName"] = methodInvokeParameters.MethodName,
                ["payload"] = methodInvokeParameters.Payload,
            };
            if (methodInvokeParameters.ResponseTimeoutInSeconds.HasValue)
            {
                bodyDict["responseTimeoutInSeconds"] = methodInvokeParameters.ResponseTimeoutInSeconds.Value;
            }
            if (methodInvokeParameters.ConnectTimeoutInSeconds.HasValue)
            {
                bodyDict["connectTimeoutInSeconds"] = methodInvokeParameters.ConnectTimeoutInSeconds.Value;
            }

            string bodyJson = JsonSerializer.Serialize(bodyDict);

            var requestUri = new Uri($"https://{hostName}{relativeUri}?api-version={IotHubApiVersion}");
            using var request = new HttpRequestMessage(HttpMethod.Post, requestUri);
            request.Headers.Authorization = new AuthenticationHeaderValue(
                "SharedAccessSignature",
                BuildSasToken(hostName, keyName, key, TimeSpan.FromMinutes(60)));
            request.Content = new StringContent(bodyJson, Encoding.UTF8, "application/json");

            Debug.WriteLine("Invoking via REST: {0}", (object)requestUri);
            using var response = await s_httpClient.SendAsync(request, CancellationToken.None).ConfigureAwait(false);
            var responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            if (!response.IsSuccessStatusCode)
            {
                throw new HttpRequestException(
                    $"Direct method invocation failed: {(int)response.StatusCode} {response.ReasonPhrase}: {responseBody}");
            }

            Debug.WriteLine("Response received:");
            Debug.WriteLine(responseBody);
            using var responseDoc = JsonDocument.Parse(responseBody);
            var root = responseDoc.RootElement;
            return new Dictionary<string, object>
            {
                { "status", root.GetProperty("status").Clone() },
                { "payload", root.TryGetProperty("payload", out var p) ? (object)p.Clone() : null }
            };
        }

        private static (string HostName, string KeyName, string Key) ParseConnectionString(string connectionString)
        {
            string hostName = null, keyName = null, key = null;
            foreach (var part in connectionString.Split(';'))
            {
                var idx = part.IndexOf('=');
                if (idx <= 0) continue;
                var name = part.Substring(0, idx);
                var value = part.Substring(idx + 1);
                if (string.Equals(name, "HostName", StringComparison.OrdinalIgnoreCase)) hostName = value;
                else if (string.Equals(name, "SharedAccessKeyName", StringComparison.OrdinalIgnoreCase)) keyName = value;
                else if (string.Equals(name, "SharedAccessKey", StringComparison.OrdinalIgnoreCase)) key = value;
            }
            if (hostName == null || keyName == null || key == null)
            {
                throw new ArgumentException("Connection string is missing HostName, SharedAccessKeyName, or SharedAccessKey");
            }
            return (hostName, keyName, key);
        }

        private static string BuildSasToken(string resourceUri, string keyName, string key, TimeSpan ttl)
        {
            var encodedResource = Uri.EscapeDataString(resourceUri);
            var expiry = (long)(DateTime.UtcNow.Add(ttl) - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalSeconds;
            var stringToSign = encodedResource + "\n" + expiry.ToString();
            using var hmac = new HMACSHA256(Convert.FromBase64String(key));
            var signature = Convert.ToBase64String(hmac.ComputeHash(Encoding.UTF8.GetBytes(stringToSign)));
            return $"sr={encodedResource}&sig={Uri.EscapeDataString(signature)}&se={expiry}&skn={Uri.EscapeDataString(keyName)}";
        }

        public async Task CleanupResourcesAsync()
        {
            if (objectMap.Count > 0)
            {
                string[] keys = new string[objectMap.Count];
                objectMap.Keys.CopyTo(keys, 0);
                foreach (var key in keys)
                {
                    await DisconnectAsync(key).ConfigureAwait(false);
                }
            }
        }

    }
}
