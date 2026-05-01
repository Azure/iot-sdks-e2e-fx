using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore;
// Added 1 line in merge
using System;
using System.Diagnostics.Tracing;
using System.Reflection;
using Microsoft.Azure.Devices.Client;
using Newtonsoft.Json;
using IO.Swagger.Controllers;

namespace IO.Swagger
{
    /// <summary>
    /// Program
    /// </summary>
    public class Program
    {
        /// <summary>
        /// Main
        /// </summary>
        /// <param name="args"></param>
        public static void Main(string[] args)
        {
            // Added 1 line in merge
            ConsoleEventListener _listener = new ConsoleEventListener("Microsoft-Azure-");

#if !SDK_NET10
            // The v2 preview SDK (previews/v2, netstandard2.0) declares
            // method-invocation Payload fields as byte[] with
            // [JsonProperty("payload")], which Newtonsoft serializes as a
            // base64 string by default. Register a global converter that
            // treats byte[] content as raw UTF-8 JSON.
            //
            // The net10.0 SDK (ewertons branch) removed DefaultPayloadConvention
            // and migrated to System.Text.Json, so none of this is needed.
            _ = DefaultPayloadConvention.Instance;
            try
            {
                FieldInfo sSettingsField = typeof(DefaultPayloadConvention)
                    .GetField("s_settings", BindingFlags.NonPublic | BindingFlags.Static);
                if (sSettingsField?.GetValue(null) is Newtonsoft.Json.JsonSerializerSettings sdkSettings)
                {
                    sdkSettings.Converters.Add(new RawJsonByteArrayConverter());
                    Console.WriteLine("Injected RawJsonByteArrayConverter into DefaultPayloadConvention.s_settings");
                }
                else
                {
                    Console.WriteLine("WARNING: could not locate DefaultPayloadConvention.s_settings");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("WARNING: failed to patch DefaultPayloadConvention.s_settings: " + ex);
            }

            try
            {
                Type serviceClientType = typeof(Microsoft.Azure.Devices.IotHubServiceClient);
                Console.WriteLine("Loaded service SDK assembly: " + serviceClientType.Assembly.FullName);

                bool injected = false;
                foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                {
                    string asmName = asm.GetName().Name ?? "";
                    if (!asmName.StartsWith("Microsoft.Azure.Devices", StringComparison.Ordinal))
                    {
                        continue;
                    }
                    foreach (Type t in asm.GetTypes())
                    {
                        if (t.Name != "JsonSerializerSettingsInitializer")
                        {
                            continue;
                        }
                        FieldInfo f = t.GetField("s_settings", BindingFlags.NonPublic | BindingFlags.Static);
                        if (f?.GetValue(null) is Newtonsoft.Json.JsonSerializerSettings svcSettings)
                        {
                            svcSettings.Converters.Add(new RawJsonByteArrayConverter());
                            Console.WriteLine($"Injected RawJsonByteArrayConverter into {t.FullName} (assembly {asmName}).s_settings");
                            injected = true;
                        }
                        else
                        {
                            Console.WriteLine($"Found {t.FullName} but s_settings field not accessible");
                        }
                    }
                }
                if (!injected)
                {
                    Console.WriteLine("WARNING: no JsonSerializerSettingsInitializer.s_settings was patched.");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("WARNING: failed to patch service JsonSerializerSettingsInitializer: " + ex);
            }

            JsonConvert.DefaultSettings = () => new Newtonsoft.Json.JsonSerializerSettings
            {
                DateParseHandling = DateParseHandling.None,
                Converters = { new RawJsonByteArrayConverter() }
            };

            try
            {
                var probeBytes = System.Text.Encoding.UTF8.GetBytes("{\"hello\":\"world\"}");
                var probeReq = new EdgeModuleDirectMethodRequest("probe", probeBytes);
                string probeJson = JsonConvert.SerializeObject(probeReq);
                Console.WriteLine("STARTUP SELFTEST (JsonConvert.SerializeObject of EdgeModuleDirectMethodRequest):");
                Console.WriteLine("  " + probeJson);
                string probeJson2 = Microsoft.Azure.Devices.Client.DefaultPayloadConvention.Instance
                    .GetType()
                    .GetMethod("Serialize", BindingFlags.NonPublic | BindingFlags.Static)
                    ?.Invoke(null, new object[] { probeReq }) as string;
                Console.WriteLine("STARTUP SELFTEST (DefaultPayloadConvention.Serialize via reflection):");
                Console.WriteLine("  " + probeJson2);
            }
            catch (Exception ex)
            {
                Console.WriteLine("STARTUP SELFTEST failed: " + ex);
            }
#endif // !SDK_NET10

            CreateWebHostBuilder(args).Build().Run();
        }

        /// <summary>
        /// Create the web host builder.
        /// </summary>
        /// <param name="args"></param>
        /// <returns>IWebHostBuilder</returns>
        public static IWebHostBuilder CreateWebHostBuilder(string[] args) =>
            WebHost.CreateDefaultBuilder(args)
                .UseStartup<Startup>()
                // added 1 line
                .UseUrls("http://*:80");
    }
}
