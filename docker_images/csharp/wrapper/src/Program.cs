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
            JsonConvert.DefaultSettings = () => new JsonSerializerSettings
            {
                DateParseHandling = DateParseHandling.None,
                Converters = { new RawJsonByteArrayConverter() }
            };

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
