// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using IO.Swagger.Models;
using Microsoft.Azure.Devices.Client;
using Microsoft.Azure.Devices.Shared;
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
        private static Dictionary<string, ModuleClient> objectMap = new Dictionary<string, ModuleClient>();
        private static Dictionary<string, ConcurrentDictionary<string, Channel<byte[]>>> inputQueues =
            new Dictionary<string, ConcurrentDictionary<string, Channel<byte[]>>>();
        private static int objectCount = 0;
        private const string modulePrefix = "module_";

        // Cache one ModuleClient per (transport) for ConnectFromEnvironment.
        // Each test fixture historically called connect_from_environment + disconnect, which
        // tore down the underlying MQTT/AMQP session and forced edgeHub to rebuild its cloud
        // proxy. With ~40 such churns in a single test session, IoT Hub's view of the module
        // becomes stale and direct method invocations from the service start failing with
        // 404103 "device isn't online" for minutes. Reusing a single underlying client
        // eliminates the storm; the client is closed when the container exits or via
        // CleanupResourcesAsync.
        private static readonly object envClientLock = new object();
        private static ModuleClient cachedEnvClient = null;
        private static string cachedEnvTransport = null;

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
            var client = ModuleClient.CreateFromConnectionString(connectionString, GlueUtils.TransportNameToType(transport));
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
            ModuleClient client;
            ModuleClient toClose = null;
            lock (envClientLock)
            {
                if (cachedEnvClient != null && cachedEnvTransport == transport)
                {
                    Console.WriteLine("Reusing cached env ModuleClient (transport={0})", transport as object);
                    client = cachedEnvClient;
                }
                else
                {
                    client = null;
                    if (cachedEnvClient != null)
                    {
                        Console.WriteLine("Cached env ModuleClient transport changed from {0} to {1}; will recreate", cachedEnvTransport as object, transport as object);
                        toClose = cachedEnvClient;
                        cachedEnvClient = null;
                        cachedEnvTransport = null;
                    }
                }
            }

            if (toClose != null)
            {
                try { await toClose.CloseAsync().ConfigureAwait(false); }
                catch (Exception ex) { Console.WriteLine("Error closing previous env client: " + ex.Message); }
            }

            if (client == null)
            {
                var newClient = await ModuleClient.CreateFromEnvironmentAsync(GlueUtils.TransportNameToType(transport)).ConfigureAwait(false);
                await newClient.OpenAsync().ConfigureAwait(false);
                lock (envClientLock)
                {
                    cachedEnvClient = newClient;
                    cachedEnvTransport = transport;
                }
                client = newClient;
            }

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
                bool isCachedEnvClient;
                lock (envClientLock)
                {
                    isCachedEnvClient = ReferenceEquals(client, cachedEnvClient);
                }
                if (isCachedEnvClient)
                {
                    // Keep the underlying connection open to avoid connection storms against
                    // edgeHub when subsequent test fixtures reconnect with the same identity.
                    // The client is closed via CleanupResourcesAsync or container exit.
                    Console.WriteLine("Skipping close: connection {0} maps to cached env client", connectionId as object);
                }
                else
                {
                    await client.CloseAsync().ConfigureAwait(false);
                    Console.WriteLine("Disconnected successfully");
                }
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

            // Register a persistent per-input handler that buffers messages
            // into a Channel so that WaitForInputMessageAsync can read them
            // without a race between set-handler and the first arriving message.
            MessageHandler handler = async (msg, context) =>
            {
                string inputName = msg.InputName ?? "";
                Console.WriteLine("Input message received on input: " + inputName);
                var channel = GetOrCreateInputChannel(connectionId, inputName);
                await channel.Writer.WriteAsync(msg.GetBytes()).ConfigureAwait(false);
                return MessageResponse.Completed;
            };

            await client.SetMessageHandlerAsync(handler, null).ConfigureAwait(false);
            Console.WriteLine("Persistent input message handler registered");
        }

        public async Task EnableMethodsAsync(string connectionId)
        {
            Console.WriteLine("EnableMethodsAsync received for " + connectionId);
        }

        private TwinCollection lastDesiredProps = null;
        private SemaphoreSlim desiredPropMutex = null;

        public async Task EnableTwinAsync(string connectionId)
        {
            Console.WriteLine("EnableTwinAsync received for " + connectionId);
            var client = objectMap[connectionId];

            DesiredPropertyUpdateCallback handler = async (props, context) =>
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
            await client.SetDesiredPropertyUpdateCallbackAsync(handler, null).ConfigureAwait(false);
            Console.WriteLine("Done enabling twin");

        }

        public async Task SendEventAsync(string connectionId, EventBody eventBody)
        {
            Console.WriteLine("sendEventAsync received for {0} with body {1}", connectionId, eventBody.Body.ToString());
            var client = objectMap[connectionId];
            await client.SendEventAsync(new Microsoft.Azure.Devices.Client.Message(GlueUtils.ObjectToBytes(eventBody.Body))).ConfigureAwait(false);
            Console.WriteLine("sendEventAsync complete");
        }

        public async Task SendOutputEventAsync(string connectionId, string outputName, EventBody eventBody)
        {
            Console.WriteLine("sendEventAsync received for {0} with output {1} and body {2}", connectionId, outputName, eventBody.Body.ToString());
            var client = objectMap[connectionId];
            string toSend = JsonConvert.SerializeObject(eventBody);
            await client.SendEventAsync(outputName, new Microsoft.Azure.Devices.Client.Message(GlueUtils.ObjectToBytes(eventBody.Body))).ConfigureAwait(false);
            Console.WriteLine("sendOutputEventAsync complete");
        }

        public async Task<EventBody> WaitForInputMessageAsync(string connectionId, string inputName)
        {
            Console.WriteLine("WaitForInputMessageAsync received for {0} with inputName {1}", connectionId, inputName);
            var channel = GetOrCreateInputChannel(connectionId, inputName);

            Console.WriteLine("Waiting for message on channel");
            byte[] bytes = await channel.Reader.ReadAsync().ConfigureAwait(false);
            Console.WriteLine("message received from channel");

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
            var request = GlueUtils.CreateMethodRequest(methodInvokeParameters);
            Console.WriteLine("Invoking");
            var response = await client.InvokeMethodAsync(deviceId, moduleId, request, CancellationToken.None).ConfigureAwait(false);
            Console.WriteLine("Response received:");
            Console.WriteLine(JsonConvert.SerializeObject(response));
            return new JObject(
                new JProperty("status", response.Status),
                new JProperty("payload", response.ResultAsJson)
            );
        }

        public async Task<object> InvokeDeviceMethodAsync(string connectionId, string deviceId, MethodInvoke methodInvokeParameters)
        {
            Console.WriteLine("InvokeDeviceMethodAsync received for {0} with deviceId {1} ", connectionId, deviceId);
            Console.WriteLine(methodInvokeParameters.ToString());
            var client = objectMap[connectionId];
            var request = GlueUtils.CreateMethodRequest(methodInvokeParameters);
            Console.WriteLine("Invoking");
            var response = await client.InvokeMethodAsync(deviceId, request, CancellationToken.None).ConfigureAwait(false);
            Console.WriteLine("Response received:");
            Console.WriteLine(JsonConvert.SerializeObject(response));
            return new JObject(
                new JProperty("status", response.Status),
                new JProperty("payload", response.ResultAsJson)
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
                Desired = lastDesiredProps
            };
        }

        public async Task<Models.Twin> GetTwinAsync(string connectionId)
        {
            Console.WriteLine("GetTwinAsync received for " + connectionId);
            var client = objectMap[connectionId];
            Microsoft.Azure.Devices.Shared.Twin t = await client.GetTwinAsync().ConfigureAwait(false);
            Console.WriteLine("Twin Received");
            Console.WriteLine(JsonConvert.SerializeObject(t));
            return new Models.Twin {
                Desired = t.Properties.Desired,
                Reported = t.Properties.Reported
            };
        }

        public async Task SendTwinPatchAsync(string connectionId, Models.Twin props)
        {
            Console.WriteLine("SendTwinPatchAsync received for " + connectionId);
            Console.WriteLine(JsonConvert.SerializeObject(props));
            var client = objectMap[connectionId];
            TwinCollection reportedProps = new TwinCollection(props.Reported as JObject, null);
            await client.UpdateReportedPropertiesAsync(reportedProps).ConfigureAwait(false);
        }

        public async Task<object> RoundtripMethodCallAsync(string connectionId, string methodName, MethodRequestAndResponse requestAndResponse)
        {
            Console.WriteLine("RoundtripMethodCallAsync received for {0} and methodName {1}", connectionId, methodName);
            Console.WriteLine(JsonConvert.SerializeObject(requestAndResponse));
            var client = objectMap[connectionId];
            var mutex = new System.Threading.SemaphoreSlim(1);
            await mutex.WaitAsync().ConfigureAwait(false);  // Grab the mutex. The handler will release it later

            MethodCallback callback = async (methodRequest, userContext) =>
            {
                Console.WriteLine("Method invocation received");

                object request = JsonConvert.DeserializeObject(methodRequest.DataAsJson);
                string received = JsonConvert.SerializeObject(new JRaw(request));
                string expected = ((Newtonsoft.Json.Linq.JToken)requestAndResponse.RequestPayload)["payload"].ToString();
                Console.WriteLine("request expected: " + expected);
                Console.WriteLine("request received: " + received);
                if (expected != received)
                {
                    Console.WriteLine("request did not match expectations");
                    Console.WriteLine("Releasing the method mutex");
                    mutex.Release();
                    return new MethodResponse(500);
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
                    return new MethodResponse(responseBytes, status);
                }
            };

            Console.WriteLine("Setting the handler");
            await client.SetMethodHandlerAsync(methodName, callback, null).ConfigureAwait(false);

            Console.WriteLine("Waiting on the method mutex");
            await mutex.WaitAsync().ConfigureAwait(false);

            Console.WriteLine("Method mutex released.  Waiting for a tiny bit.");  // Otherwise, the connection might close before the response is actually sent
            await Task.Delay(100).ConfigureAwait(false);

            Console.WriteLine("Nulling the handler");
            await client.SetMethodHandlerAsync(methodName, null, null).ConfigureAwait(false);

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

            // DisconnectAsync intentionally skips closing the cached env client to avoid
            // edgeHub connection storms across test fixtures. CleanupResourcesAsync is the
            // session-level teardown, so close it here.
            ModuleClient envClient;
            lock (envClientLock)
            {
                envClient = cachedEnvClient;
                cachedEnvClient = null;
                cachedEnvTransport = null;
            }
            if (envClient != null)
            {
                try { await envClient.CloseAsync().ConfigureAwait(false); }
                catch (Exception ex) { Console.WriteLine("Error closing cached env client: " + ex.Message); }
            }
        }
    }
}
