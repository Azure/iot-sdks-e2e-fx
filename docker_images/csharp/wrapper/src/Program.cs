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

            // The v2 preview SDK declares method-invocation Payload fields as
            // byte[] with [JsonProperty("payload")], which Newtonsoft serializes
            // as a base64 string by default. Register a global converter that
            // treats byte[] content as raw UTF-8 JSON, so module-to-module and
            // module-to-device direct method invocations round-trip correctly.
            //
            // The v2 SDK's HTTP transport (HttpClientHelper.PostAsync) calls
            // DefaultPayloadConvention.Serialize(entity), which calls
            // JsonConvert.SerializeObject(obj) with no explicit settings.
            // DefaultPayloadConvention's private constructor sets
            // JsonConvert.DefaultSettings to its own (converter-less) static
            // s_settings. Two complementary fixes ensure our converter is
            // applied:
            //   (1) Touch DefaultPayloadConvention.Instance to trigger its
            //       constructor, then overwrite JsonConvert.DefaultSettings.
            //   (2) Inject our converter directly into the SDK's private
            //       s_settings via reflection, so even if the SDK ever
            //       resolves settings via that exact instance, our converter
            //       still applies.
            // (Preserve DateParseHandling.None for SDK timestamp compatibility.)
            _ = DefaultPayloadConvention.Instance;
            try
            {
                FieldInfo sSettingsField = typeof(DefaultPayloadConvention)
                    .GetField("s_settings", BindingFlags.NonPublic | BindingFlags.Static);
                if (sSettingsField?.GetValue(null) is JsonSerializerSettings sdkSettings)
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

            // The service SDK's IotHubServiceClient.InitializeSubclients()
            // unconditionally overwrites JsonConvert.DefaultSettings with a
            // delegate returning Microsoft.Azure.Devices.JsonSerializerSettingsInitializer
            // .s_settings (which has no Converters). Inject our converter into
            // that static settings instance too, by reflection across loaded
            // service-SDK assemblies.
            try
            {
                // Force the service SDK assembly to load so its types are
                // available for reflection. Using FullName forces actual use
                // so the JIT cannot elide the typeof.
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
                        if (f?.GetValue(null) is JsonSerializerSettings svcSettings)
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

            JsonConvert.DefaultSettings = () => new JsonSerializerSettings
            {
                DateParseHandling = DateParseHandling.None,
                Converters = { new RawJsonByteArrayConverter() }
            };

            // Self-test: serialize an EdgeModuleDirectMethodRequest with a known
            // payload and log the result so we can see whether our converter is
            // actually being picked up by JsonConvert.SerializeObject(obj).
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
