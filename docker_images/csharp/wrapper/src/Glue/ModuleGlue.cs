// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using IO.Swagger.Models;
using Microsoft.Azure.Devices.Client;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;

#pragma warning disable CA1304, CA1305, CA1307 // string function could vary with locale
#pragma warning disable CA1822 // method could be marked static
#pragma warning disable CA1822 // parameter is never used
#pragma warning disable CS1998 // async method lacks await operator

namespace IO.Swagger.Controllers
{
    /// <summary>
    /// Object which glues the swagger generated wrappers to the various IoTHub SDKs
    /// </summary>
    internal class ModuleGlue
    {
        private static Dictionary<string, IotHubModuleClient> objectMap = new Dictionary<string, IotHubModuleClient>();
        private static Dictionary<string, ConcurrentDictionary<string, Channel<byte[]>>> inputQueues =
            new Dictionary<string, ConcurrentDictionary<string, Channel<byte[]>>>();
        private static int objectCount = 0;
        private const string modulePrefix = "module_";

        private static Channel<byte[]> GetOrCreateInputChannel(string connectionId, string inputName)
        {
            ConcurrentDictionary<string, Channel<byte[]>> perConnection;
            lock (inputQueues)
            {
                if (!inputQueues.TryGetValue(connectionId, out perConnection))
                {
                    perConnection = new ConcurrentDictionary<string, Channel<byte[]>>();
                    inputQueues[connectionId] = perConnection;
                }
            }
            return perConnection.GetOrAdd(inputName, _ => Channel.CreateUnbounded<byte[]>());
        }

        public ModuleGlue()
        {
        }

        public async Task<ConnectResponse> ConnectAsync(string transport, string connectionString, Certificate caCertificate)
        {
            Console.WriteLine("ConnectAsync for " + transport);
            var client = new IotHubModuleClient(connectionString, GlueUtils.TransportNameToOptions(transport));
            await client.OpenAsync().ConfigureAwait(false);
            var connectionId = modulePrefix + Convert.ToString(++objectCount);
            Console.WriteLine("Connected successfully.  Connection Id = " + connectionId);
            objectMap[connectionId] = client;
            return new ConnectResponse
            {
                ConnectionId = connectionId
            };
        }

        public async Task<ConnectResponse> ConnectFromEnvironmentAsync(string transport)
        {
            var client = await IotHubModuleClient.CreateFromEnvironmentAsync(GlueUtils.TransportNameToOptions(transport)).ConfigureAwait(false);
            await client.OpenAsync().ConfigureAwait(false);
            var connectionId = modulePrefix + Convert.ToString(++objectCount);
            objectMap[connectionId] = client;
            return new ConnectResponse
            {
                ConnectionId = connectionId
            };
        }

        public async Task DisconnectAsync(string connectionId)
        {
            Console.WriteLine("DisconnectAsync received for " + connectionId);
            if (objectMap.ContainsKey(connectionId))
            {
                var client = objectMap[connectionId];
                objectMap.Remove(connectionId);
                lock (inputQueues)
                {
                    inputQueues.Remove(connectionId);
                }
                await client.CloseAsync().ConfigureAwait(false);
                Console.WriteLine("Disconnected successfully");
            }
            else
            {
                Console.WriteLine("Client already disconnected.  Nothing to to do.");
            }
        }

        public async Task EnableInputMessagesAsync(string connectionId)
        {
            Console.WriteLine("EnableInputMessageAsync received for " + connectionId);
            var client = objectMap[connectionId];

            // Register a single, persistent handler that queues incoming messages per input name.
            // The previous implementation registered/unregistered the handler inside each
            // WaitForInputMessageAsync call, which caused messages that arrived before the wait
            // started (or for a different input name than the one currently being awaited) to be
            // silently dropped.
            Func<IncomingMessage, Task<MessageAcknowledgement>> handler = async (msg) =>
            {
                Console.WriteLine("message received for input: " + msg.InputName);
                if (string.IsNullOrEmpty(msg.InputName))
                {
                    return MessageAcknowledgement.Abandon;
                }
                var channel = GetOrCreateInputChannel(connectionId, msg.InputName);
                await channel.Writer.WriteAsync(msg.GetPayloadAsBytes()).ConfigureAwait(false);
                return MessageAcknowledgement.Complete;
            };

            Console.WriteLine("Setting persistent input handler");
            await client.SetIncomingMessageCallbackAsync(handler).ConfigureAwait(false);
        }

        public async Task EnableMethodsAsync(string connectionId)
        {
            Console.WriteLine("EnableMethodsAsync received for " + connectionId);
        }

        private DesiredProperties lastDesiredProps = null;
        private SemaphoreSlim desiredPropMutex = null;

        public async Task EnableTwinAsync(string connectionId)
        {
            Console.WriteLine("EnableTwinAsync received for " + connectionId);
            var client = objectMap[connectionId];

            Func<DesiredProperties, Task> handler = async (props) =>
            {
                Console.WriteLine("patch received");
                lastDesiredProps = props;
                if (desiredPropMutex == null)
                {
                    Console.WriteLine("No mutex to release.  nobody is listening for this patch.");
                }
                else
                {
                    Console.WriteLine("releasing patch mutex");
                    desiredPropMutex.Release();
                    desiredPropMutex = null;
                }
            };

            Console.WriteLine("setting patch handler");
            await client.SetDesiredPropertyUpdateCallbackAsync(handler).ConfigureAwait(false);
            Console.WriteLine("Done enabling twin");

        }

        public async Task SendEventAsync(string connectionId, EventBody eventBody)
        {
            Console.WriteLine("sendEventAsync received for {0} with body {1}", connectionId, eventBody.Body.ToString());
            var client = objectMap[connectionId];
            await client.SendTelemetryAsync(new TelemetryMessage(GlueUtils.ObjectToBytes(eventBody.Body))).ConfigureAwait(false);
            Console.WriteLine("sendEventAsync complete");
        }

        public async Task SendOutputEventAsync(string connectionId, string outputName, EventBody eventBody)
        {
            Console.WriteLine("sendEventAsync received for {0} with output {1} and body {2}", connectionId, outputName, eventBody.Body.ToString());
            var client = objectMap[connectionId];
            await client.SendMessageToRouteAsync(outputName, new TelemetryMessage(GlueUtils.ObjectToBytes(eventBody.Body))).ConfigureAwait(false);
            Console.WriteLine("sendOutputEventAsync complete");
        }

        public async Task<EventBody> WaitForInputMessageAsync(string connectionId, string inputName)
        {
            Console.WriteLine("WaitForInputMessageAsync received for {0} with inputName {1}", connectionId, inputName);

            // The persistent handler installed in EnableInputMessagesAsync queues incoming
            // messages per input name. Just read the next queued message for this input.
            var channel = GetOrCreateInputChannel(connectionId, inputName);

            Console.WriteLine("Waiting for next queued message on input {0}", inputName as object);
            byte[] bytes = await channel.Reader.ReadAsync().ConfigureAwait(false);
            Console.WriteLine("Dequeued message for input {0}", inputName as object);

            string s = Encoding.UTF8.GetString(bytes);
            Console.WriteLine("message = {0}", s as object);
            object result;
            try
            {
                result = JsonConvert.DeserializeObject(s);
            }
            catch(JsonReaderException)
            {
                result = s;
            }
            return new Models.EventBody
            {
                Body = result
            };
        }

        public async Task<object> InvokeModuleMethodAsync(string connectionId, string deviceId, string moduleId, MethodInvoke methodInvokeParameters)
        {
            Console.WriteLine("InvokeModuleMethodAsync received for {0} with deviceId {1} and moduleId {2}", connectionId, deviceId, moduleId);
            Console.WriteLine(methodInvokeParameters.ToString());
            var client = objectMap[connectionId];
            var request = GlueUtils.CreateEdgeModuleDirectMethodRequest(methodInvokeParameters);
            Console.WriteLine("Invoking");
            var response = await client.InvokeMethodAsync(deviceId, moduleId, request, CancellationToken.None).ConfigureAwait(false);
            Console.WriteLine("Response received:");
            Console.WriteLine(JsonConvert.SerializeObject(response));
            return new JObject(
                new JProperty("status", response.Status),
                new JProperty("payload", GlueUtils.PayloadBytesToJson(response.GetPayloadAsBytes()))
            );
        }

        public async Task<object> InvokeDeviceMethodAsync(string connectionId, string deviceId, MethodInvoke methodInvokeParameters)
        {
            Console.WriteLine("InvokeDeviceMethodAsync received for {0} with deviceId {1} ", connectionId, deviceId);
            Console.WriteLine(methodInvokeParameters.ToString());
            var client = objectMap[connectionId];
            var request = GlueUtils.CreateEdgeModuleDirectMethodRequest(methodInvokeParameters);
            Console.WriteLine("Invoking");
            var response = await client.InvokeMethodAsync(deviceId, request, CancellationToken.None).ConfigureAwait(false);
            Console.WriteLine("Response received:");
            Console.WriteLine(JsonConvert.SerializeObject(response));
            return new JObject(
                new JProperty("status", response.Status),
                new JProperty("payload", GlueUtils.PayloadBytesToJson(response.GetPayloadAsBytes()))
            );
        }

        public async Task<Models.Twin> WaitForDesiredPropertyPatchAsync(string connectionId)
        {
            // Since there's no way to un-register for a patch, we have a global patch handler.  We keep the
            // "last desired props received" in a member varaible along with a mutex to trigger when this changes.
            // Not very cool and not very thread safe :(
            Console.WriteLine("WaitForDesiredPropertyPatchAsync received for " + connectionId);
            var client = objectMap[connectionId];
            var mutex = new System.Threading.SemaphoreSlim(1);
            await mutex.WaitAsync().ConfigureAwait(false);  // Grab the mutex. The handler will release it later
            desiredPropMutex = mutex;

            Console.WriteLine("Waiting for patch");
            await mutex.WaitAsync().ConfigureAwait(false);
            Console.WriteLine("mutex triggered.");

            Console.WriteLine("Returning patch:");
            Console.WriteLine(JsonConvert.SerializeObject(lastDesiredProps));
            return new Models.Twin {
                Desired = JObject.Parse(lastDesiredProps.GetSerializedString())
            };
        }

        public async Task<Models.Twin> GetTwinAsync(string connectionId)
        {
            Console.WriteLine("GetTwinAsync received for " + connectionId);
            var client = objectMap[connectionId];
            TwinProperties t = await client.GetTwinPropertiesAsync().ConfigureAwait(false);
            Console.WriteLine("Twin Received");
            Console.WriteLine(JsonConvert.SerializeObject(t));
            return new Models.Twin {
                Desired = JObject.Parse(t.Desired.GetSerializedString()),
                Reported = JObject.Parse(t.Reported.GetSerializedString())
            };
        }

        public async Task SendTwinPatchAsync(string connectionId, Models.Twin props)
        {
            Console.WriteLine("SendTwinPatchAsync received for " + connectionId);
            Console.WriteLine(JsonConvert.SerializeObject(props));
            var client = objectMap[connectionId];
            var reportedProps = new ReportedProperties();
            foreach (var p in (props.Reported as JObject).Properties())
            {
                reportedProps[p.Name] = p.Value.Type == JTokenType.Null ? null : p.Value.ToObject<object>();
            }
            await client.UpdateReportedPropertiesAsync(reportedProps).ConfigureAwait(false);
        }

        public async Task<object> RoundtripMethodCallAsync(string connectionId, string methodName, MethodRequestAndResponse requestAndResponse)
        {
            Console.WriteLine("RoundtripMethodCallAsync received for {0} and methodName {1}", connectionId, methodName);
            Console.WriteLine(JsonConvert.SerializeObject(requestAndResponse));
            var client = objectMap[connectionId];
            var mutex = new System.Threading.SemaphoreSlim(1);
            await mutex.WaitAsync().ConfigureAwait(false);  // Grab the mutex. The handler will release it later

            Func<DirectMethodRequest, Task<DirectMethodResponse>> callback = async (methodRequest) =>
            {
                if (methodRequest.MethodName != methodName)
                {
                    return new DirectMethodResponse(404);
                }

                Console.WriteLine("Method invocation received");

                object request = JsonConvert.DeserializeObject(Encoding.UTF8.GetString(methodRequest.GetPayload()));
                string received = JsonConvert.SerializeObject(new JRaw(request));
                string expected = ((Newtonsoft.Json.Linq.JToken)requestAndResponse.RequestPayload)["payload"].ToString();
                Console.WriteLine("request expected: " + expected);
                Console.WriteLine("request received: " + received);
                if (expected != received)
                {
                    Console.WriteLine("request did not match expectations");
                    Console.WriteLine("Releasing the method mutex");
                    mutex.Release();
                    return new DirectMethodResponse(500);
                }
                else
                {
                    int status = 200;
                    if (requestAndResponse.StatusCode != null)
                    {
                        status = (int)requestAndResponse.StatusCode;
                    }

                    byte[] responseBytes = GlueUtils.ObjectToBytes(requestAndResponse.ResponsePayload);

                    Console.WriteLine("Releasing the method mutex");
                    mutex.Release();

                    Console.WriteLine("Returning the result");
                    return new DirectMethodResponse(status) { Payload = responseBytes };
                }
            };

            Console.WriteLine("Setting the handler");
            await client.SetDirectMethodCallbackAsync(callback).ConfigureAwait(false);

            Console.WriteLine("Waiting on the method mutex");
            await mutex.WaitAsync().ConfigureAwait(false);

            Console.WriteLine("Method mutex released.  Waiting for a tiny bit.");  // Otherwise, the connection might close before the response is actually sent
            await Task.Delay(100).ConfigureAwait(false);

            Console.WriteLine("Nulling the handler");
            await client.SetDirectMethodCallbackAsync(null).ConfigureAwait(false);

            Console.WriteLine("RoundtripMethodCallAsync is complete");
            return new object();
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
