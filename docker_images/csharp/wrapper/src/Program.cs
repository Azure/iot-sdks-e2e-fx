using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore;
using System;
using System.Diagnostics.Tracing;
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
            ConsoleEventListener _listener = new ConsoleEventListener("Microsoft-Azure-");

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
