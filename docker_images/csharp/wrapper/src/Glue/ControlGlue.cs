// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
using System;
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
    internal class ControlGlue
    {
        public ControlGlue()
        {
        }


        public async Task CleanupResourcesAsync()
        {
            await ModuleApiController.module_glue.CleanupResourcesAsync().ConfigureAwait(false);
            await RegistryApiController.registry_glue.CleanupResourcesAsync().ConfigureAwait(false);
            await ServiceApiController.service_glue.CleanupResourcesAsync().ConfigureAwait(false);
        }

        public async Task PrintMessageAsync(String message)
        {
            Console.WriteLine(message);
        }

        public async Task<object> GetCapabilities()
        {
            var caps = new
            {
                flags = new
                {
                    supports_async = false,
                    security_messages = false,
                    v2_connect_group = false,
                    dropped_connection_tests = false,
                    net_control_app = false
                },
                skip_list = new [] { "module_under_test_has_device_wrapper" },
            };
            return caps;
        }
    }
}
