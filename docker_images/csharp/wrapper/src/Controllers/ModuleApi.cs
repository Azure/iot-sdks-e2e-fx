/*
 * Azure IOT End-to-End Test Wrapper Rest Api
 *
 * REST API definition for End-to-end testing of the Azure IoT SDKs.  All SDK APIs that are tested by our E2E tests need to be defined in this file.  This file takes some liberties with the API definitions.  In particular, response schemas are undefined, and error responses are also undefined.
 *
 * OpenAPI spec version: 1.0.0
 *
 * Generated by: https://github.com/swagger-api/swagger-codegen.git
 */

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.WebUtilities;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Primitives;
using Swashbuckle.AspNetCore.SwaggerGen;
using Newtonsoft.Json;
using System.ComponentModel.DataAnnotations;
using IO.Swagger.Attributes;
using IO.Swagger.Models;

namespace IO.Swagger.Controllers
{
    /// <summary>
    ///
    /// </summary>
    public class ModuleApiController : Controller
    {
        /// <summary>
        /// Connect to the azure IoT Hub as a module
        /// </summary>

        /// <param name="transportType">Transport to use</param>
        /// <param name="connectionString">connection string</param>
        /// <param name="caCertificate"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/connect/{transportType}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleConnect")]
        [SwaggerResponse(statusCode: 200, type: typeof(ConnectResponse), description: "OK")]
        public virtual IActionResult ModuleConnect([FromRoute][Required]string transportType, [FromQuery][Required()]string connectionString, [FromBody]Certificate caCertificate)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(ConnectResponse));

            string exampleJson = null;
            exampleJson = "{\n  \"connectionId\" : \"connectionId\"\n}";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<ConnectResponse>(exampleJson)
            : default(ConnectResponse);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Connect the module
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/connect2")]
        [ValidateModelState]
        [SwaggerOperation("ModuleConnect2")]
        public virtual IActionResult ModuleConnect2([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Connect to the azure IoT Hub as a module using the environment variables
        /// </summary>

        /// <param name="transportType">Transport to use</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/connectFromEnvironment/{transportType}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleConnectFromEnvironment")]
        [SwaggerResponse(statusCode: 200, type: typeof(ConnectResponse), description: "OK")]
        public virtual IActionResult ModuleConnectFromEnvironment([FromRoute][Required]string transportType)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(ConnectResponse));

            string exampleJson = null;
            exampleJson = "{\n  \"connectionId\" : \"connectionId\"\n}";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<ConnectResponse>(exampleJson)
            : default(ConnectResponse);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Create a module client from a connection string
        /// </summary>

        /// <param name="transportType">Transport to use</param>
        /// <param name="connectionString">connection string</param>
        /// <param name="caCertificate"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/createFromConnectionstring/{transportType}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleCreateFromConnectionString")]
        [SwaggerResponse(statusCode: 200, type: typeof(ConnectResponse), description: "OK")]
        public virtual IActionResult ModuleCreateFromConnectionString([FromRoute][Required]string transportType, [FromQuery][Required()]string connectionString, [FromBody]Certificate caCertificate)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(ConnectResponse));

            string exampleJson = null;
            exampleJson = "{\n  \"connectionId\" : \"connectionId\"\n}";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<ConnectResponse>(exampleJson)
            : default(ConnectResponse);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Create a module client using the EdgeHub environment
        /// </summary>

        /// <param name="transportType">Transport to use</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/createFromEnvironment/{transportType}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleCreateFromEnvironment")]
        [SwaggerResponse(statusCode: 200, type: typeof(ConnectResponse), description: "OK")]
        public virtual IActionResult ModuleCreateFromEnvironment([FromRoute][Required]string transportType)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(ConnectResponse));

            string exampleJson = null;
            exampleJson = "{\n  \"connectionId\" : \"connectionId\"\n}";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<ConnectResponse>(exampleJson)
            : default(ConnectResponse);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Create a module client from X509 credentials
        /// </summary>

        /// <param name="transportType">Transport to use</param>
        /// <param name="x509"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/createFromX509/{transportType}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleCreateFromX509")]
        [SwaggerResponse(statusCode: 200, type: typeof(ConnectResponse), description: "OK")]
        public virtual IActionResult ModuleCreateFromX509([FromRoute][Required]string transportType, [FromBody]Object x509)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(ConnectResponse));

            string exampleJson = null;
            exampleJson = "{\n  \"connectionId\" : \"connectionId\"\n}";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<ConnectResponse>(exampleJson)
            : default(ConnectResponse);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Disonnect and destroy the module client
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/destroy")]
        [ValidateModelState]
        [SwaggerOperation("ModuleDestroy")]
        public virtual IActionResult ModuleDestroy([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Disconnect the module
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/disconnect")]
        [ValidateModelState]
        [SwaggerOperation("ModuleDisconnect")]
        public virtual IActionResult ModuleDisconnect([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Disonnect the module
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/disconnect2")]
        [ValidateModelState]
        [SwaggerOperation("ModuleDisconnect2")]
        public virtual IActionResult ModuleDisconnect2([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Enable input messages
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/enableInputMessages")]
        [ValidateModelState]
        [SwaggerOperation("ModuleEnableInputMessages")]
        public virtual IActionResult ModuleEnableInputMessages([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Enable methods
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/enableMethods")]
        [ValidateModelState]
        [SwaggerOperation("ModuleEnableMethods")]
        public virtual IActionResult ModuleEnableMethods([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Enable module twins
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/enableTwin")]
        [ValidateModelState]
        [SwaggerOperation("ModuleEnableTwin")]
        public virtual IActionResult ModuleEnableTwin([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// get the current connection status
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpGet]
        [Route("/module/{connectionId}/connectionStatus")]
        [ValidateModelState]
        [SwaggerOperation("ModuleGetConnectionStatus")]
        [SwaggerResponse(statusCode: 200, type: typeof(string), description: "OK")]
        public virtual IActionResult ModuleGetConnectionStatus([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(string));

            string exampleJson = null;
            exampleJson = "";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<string>(exampleJson)
            : default(string);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Get the device twin
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpGet]
        [Route("/module/{connectionId}/twin")]
        [ValidateModelState]
        [SwaggerOperation("ModuleGetTwin")]
        [SwaggerResponse(statusCode: 200, type: typeof(Object), description: "OK")]
        public virtual IActionResult ModuleGetTwin([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(Object));

            string exampleJson = null;
            exampleJson = "\"{}\"";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<Object>(exampleJson)
            : default(Object);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// call the given method on the given device
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="deviceId"></param>
        /// <param name="methodInvokeParameters"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/deviceMethod/{deviceId}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleInvokeDeviceMethod")]
        [SwaggerResponse(statusCode: 200, type: typeof(Object), description: "OK")]
        public virtual IActionResult ModuleInvokeDeviceMethod([FromRoute][Required]string connectionId, [FromRoute][Required]string deviceId, [FromBody]Object methodInvokeParameters)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(Object));

            string exampleJson = null;
            exampleJson = "\"{}\"";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<Object>(exampleJson)
            : default(Object);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// call the given method on the given module
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="deviceId"></param>
        /// <param name="moduleId"></param>
        /// <param name="methodInvokeParameters"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/moduleMethod/{deviceId}/{moduleId}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleInvokeModuleMethod")]
        [SwaggerResponse(statusCode: 200, type: typeof(Object), description: "OK")]
        public virtual IActionResult ModuleInvokeModuleMethod([FromRoute][Required]string connectionId, [FromRoute][Required]string deviceId, [FromRoute][Required]string moduleId, [FromBody]Object methodInvokeParameters)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(Object));

            string exampleJson = null;
            exampleJson = "\"{}\"";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<Object>(exampleJson)
            : default(Object);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Updates the device twin
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="props"></param>
        /// <response code="200">OK</response>
        [HttpPatch]
        [Route("/module/{connectionId}/twin")]
        [ValidateModelState]
        [SwaggerOperation("ModulePatchTwin")]
        public virtual IActionResult ModulePatchTwin([FromRoute][Required]string connectionId, [FromBody]Object props)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Reconnect the module
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="forceRenewPassword">True to force SAS renewal</param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/reconnect")]
        [ValidateModelState]
        [SwaggerOperation("ModuleReconnect")]
        public virtual IActionResult ModuleReconnect([FromRoute][Required]string connectionId, [FromQuery]bool? forceRenewPassword)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Wait for a method call, verify the request, and return the response.
        /// </summary>
        /// <remarks>This is a workaround to deal with SDKs that only have method call operations that are sync.  This function responds to the method with the payload of this function, and then returns the method parameters.  Real-world implemenatations would never do this, but this is the only same way to write our test code right now (because the method handlers for C, Java, and probably Python all return the method response instead of supporting an async method call)</remarks>
        /// <param name="connectionId">Id for the connection</param>
        /// <param name="methodName">name of the method to handle</param>
        /// <param name="requestAndResponse"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/roundtripMethodCall/{methodName}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleRoundtripMethodCall")]
        public virtual IActionResult ModuleRoundtripMethodCall([FromRoute][Required]string connectionId, [FromRoute][Required]string methodName, [FromBody]RoundtripMethodCallBody requestAndResponse)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Send an event
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="eventBody"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/event")]
        [ValidateModelState]
        [SwaggerOperation("ModuleSendEvent")]
        public virtual IActionResult ModuleSendEvent([FromRoute][Required]string connectionId, [FromBody]Object eventBody)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// Send an event to a module output
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="outputName"></param>
        /// <param name="eventBody"></param>
        /// <response code="200">OK</response>
        [HttpPut]
        [Route("/module/{connectionId}/outputEvent/{outputName}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleSendOutputEvent")]
        public virtual IActionResult ModuleSendOutputEvent([FromRoute][Required]string connectionId, [FromRoute][Required]string outputName, [FromBody]Object eventBody)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200);


            throw new NotImplementedException();
        }

        /// <summary>
        /// wait for the current connection status to change and return the changed status
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpGet]
        [Route("/module/{connectionId}/connectionStatusChange")]
        [ValidateModelState]
        [SwaggerOperation("ModuleWaitForConnectionStatusChange")]
        [SwaggerResponse(statusCode: 200, type: typeof(string), description: "OK")]
        public virtual IActionResult ModuleWaitForConnectionStatusChange([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(string));

            string exampleJson = null;
            exampleJson = "";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<string>(exampleJson)
            : default(string);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Wait for the next desired property patch
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <response code="200">OK</response>
        [HttpGet]
        [Route("/module/{connectionId}/twinDesiredPropPatch")]
        [ValidateModelState]
        [SwaggerOperation("ModuleWaitForDesiredPropertiesPatch")]
        [SwaggerResponse(statusCode: 200, type: typeof(Object), description: "OK")]
        public virtual IActionResult ModuleWaitForDesiredPropertiesPatch([FromRoute][Required]string connectionId)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(Object));

            string exampleJson = null;
            exampleJson = "\"{}\"";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<Object>(exampleJson)
            : default(Object);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }

        /// <summary>
        /// Wait for a message on a module input
        /// </summary>

        /// <param name="connectionId">Id for the connection</param>
        /// <param name="inputName"></param>
        /// <response code="200">OK</response>
        [HttpGet]
        [Route("/module/{connectionId}/inputMessage/{inputName}")]
        [ValidateModelState]
        [SwaggerOperation("ModuleWaitForInputMessage")]
        [SwaggerResponse(statusCode: 200, type: typeof(string), description: "OK")]
        public virtual IActionResult ModuleWaitForInputMessage([FromRoute][Required]string connectionId, [FromRoute][Required]string inputName)
        {
            //TODO: Uncomment the next line to return response 200 or use other options such as return this.NotFound(), return this.BadRequest(..), ...
            // return StatusCode(200, default(string));

            string exampleJson = null;
            exampleJson = "";

            var example = exampleJson != null
            ? JsonConvert.DeserializeObject<string>(exampleJson)
            : default(string);
            //TODO: Change the data returned
            return new ObjectResult(example);
        }
    }
}
