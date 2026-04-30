using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore;
// Added 1 line in merge
using System.Diagnostics.Tracing;
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
            JsonConvert.DefaultSettings = () => new JsonSerializerSettings
            {
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
