// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Newtonsoft.Json;
using IO.Swagger.Models;
using Microsoft.Azure.Devices;
using System.Diagnostics;
using Newtonsoft.Json.Linq;
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
                client.Dispose();
            }
        }

        public async Task<object> InvokeModuleMethodAsync(string connectionId, string deviceId, string moduleId, MethodInvoke methodInvokeParameters)
        {
            Debug.WriteLine("InvokeModuleMethodAsync received for {0} with deviceId {1} and moduleId {2}", connectionId, deviceId, moduleId);
            Debug.WriteLine(methodInvokeParameters.ToString());
            var client = objectMap[connectionId];
            var request = GlueUtils.CreateDirectMethodServiceRequest(methodInvokeParameters);
            Debug.WriteLine("Invoking");
            var response = await client.DirectMethods.InvokeAsync(deviceId, moduleId, request, CancellationToken.None).ConfigureAwait(false);
            Debug.WriteLine("Response received:");
            Debug.WriteLine(JsonConvert.SerializeObject(response));
            return new JObject(
                new JProperty("status", response.Status),
                new JProperty("payload", response.JsonPayload.GetRawText())
            );
        }

        public async Task<object> InvokeDeviceMethodAsync(string connectionId, string deviceId, MethodInvoke methodInvokeParameters)
        {
            Debug.WriteLine("InvokeDeviceMethodAsync received for {0} with deviceId {1} ", connectionId, deviceId);
            Debug.WriteLine(methodInvokeParameters.ToString());
            var client = objectMap[connectionId];
            var request = GlueUtils.CreateDirectMethodServiceRequest(methodInvokeParameters);
            Debug.WriteLine("Invoking");
            var response = await client.DirectMethods.InvokeAsync(deviceId, request, CancellationToken.None).ConfigureAwait(false);
            Debug.WriteLine("Response received:");
            Debug.WriteLine(JsonConvert.SerializeObject(response));
            return new JObject(
                new JProperty("status", response.Status),
                new JProperty("payload", response.JsonPayload.GetRawText())
            );
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
