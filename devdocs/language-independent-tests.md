
## (10,000 feet) Major Goal: one set of tests for all languages
One of our goals is to have a single test script that can run across multiple SDKs.  This will allow us to get consistent coverage and save us the trouble of re-writing every single test case in every single language.

As an example, we want to have a test case like this.  We chose Python as the language for our test scripting because it's quick and easy.  We could have just as easily chosen a different language.

(the actual test case has extra stuff, logging mostly, that was removed from this snippet)

```
def test_module_send_event_to_iothub():
  # connect the module client
  module_client = connections.connect_test_module_client()
  # connect the eventhub client
  eventhub_client = connections.connect_eventhub_client()

  # start listening for events from eventhub
  eventhub_client.enable_telemetry()
  input_thread = eventhub_client.wait_for_event_async(environment.edge_device_id)

  # create a random message and sent it from the module client
  sent_message =  test_utilities.max_random_string()
  module_client.send_event(sent_message)

  # wait for it to arrive at eventhub and verify that it's correct
  received_message = input_thread.get(test_utilities.default_eventhub_timeout)
  assert(received_message  == sent_message)

  # cleanup
  module_client.disconnect()
  eventhub_client.disconnect()
```

When `connections.connect_test_module_client()` is called, we want the node test code to do the following:
```
    ModuleClient.fromEnvironment(transportType, function(err, client) {
      if (err) {
        callback(err);
      } else {
        client.open(function(err) {
          callback(err)
        }
      }
    }
```

and in c, we want the code to do the following:
```
    IOTHUB_MODULE_CLIENT_HANDLE client;
    IOTHUB_CLIENT_TRANSPORT_PROVIDER protocol = MQTT_Protocol;
    if ((client = IoTHubModuleClient_CreateFromEnvironment(protocol)) == NULL)
    {
      // return failure
    }
    else
    {
      // return success
    }
```

We accomplish this by wrapping all of our SDKs in a way that they can all be called by the same test scripts.  The oversimplified picture looks like this.  The "Magic Layer" is what most of this project is about.  Please hold your disbelief and don't worry about "how" until later.
```
+------------------------------------------------------+
|               Python Test Scripts                    |
+------------------------------------------------------+
+------------------------------------------------------+
|                   Magic Layer                        |
+------------------------------------------------------+
+------------------------------------------------------+
|                   Node.js SDK                        |
+------------------------------------------------------+
```

And, for C, it would look like this
```
+------------------------------------------------------+
|          Exact Same Python Test Scripts              |
+------------------------------------------------------+
+------------------------------------------------------+
|          Slightly Different Magic Layer              |
+------------------------------------------------------+
+------------------------------------------------------+
|                      C SDK                           |
+------------------------------------------------------+
```

## (5000 feet) zooming in on the "Magic Layer"

In order to have a piece of python code call into different language SDKs, we need some sort of interop layer.  There are many different options here with many different tradeoffs.  We chose to use a REST api over HTTP for interop.  This may seem heavy, but it supports all of our languages and it's easy to get up and running using swagger codegen tools.  It also lets us talk across processes, across machines, and into containers without much difficulty.  This ability to cross boundaries might feel like a "nice to have" right now, but it becomes more important later on.

(For the record, our current effort is focused on using swagger as a tool for interop, but the layering of the architecture could support other interop technologies in the future for environments that can't support a full REST server on the client.)

With this in mind, when we zoom in a little bit, we see the following picture:
```
     +-----------------------------------------------------------+
     | test runner                                               |
     |                                                           |
     | +------------------------------------------------------+  |
     | |               Python Test Scripts                    |  |
     | +------------------------------------------------------+  |
     | +------------------------------------------------------+  |
     | |             Python code to serialize                 |  |
     | |              script calls into REST                  |  |
     | |         (auto+generated from swagger file)           |  |
     | +------------------------------------------------------+  |
     +-----------------------------------------------------------+
                              +----+
                              |    |
                              |    |
                              |    |
                              |HTTP|
                              |pipe|
                              |    |
                              |    |
                              |    |
                              +----+
    +------------------------------------------------------------+
    | node.js test wrapper app                                   |
    |                                                            |
    |  +------------------------------------------------------+  |
    |  |               Node code to deserialize               |  |
    |  |                     REST calls                       |  |
    |  |         (auto+generated from swagger file)           |  |
    |  +------------------------------------------------------+  |
    |  +------------------------------------------------------+  |
    |  |         Hand+written glue that connects auto+        |  |
    |  |         generated code to our Node SDK               |  |
    |  +------------------------------------------------------+  |
    |  +------------------------------------------------------+  |
    |  +                   Node.js SDK                        +  |
    |  +------------------------------------------------------+  |
    +------------------------------------------------------------+
```

In the node example, `module_client = connections.connect_test_module_client()` results in `PUT` call to `/module/connectFromEnvironment/mqtt`

Which then goes over an HTTP pipe to the NodeJS wrapper app, where it gets deserialized and ends up calling `ModuleClient.fromEnvironment(transportType, function(err, client)`

Because the test code needs to call into this client object, it needs to be able to refer to it, so the NodeJS wrapper app puts the client into a dictionary and returns a name for it, called the `connectionId`.  Lets say the test code calls the `client` object above by the name `module_01`.  It can return the string `module_01` to the test code, and when the test code needs to refer to this `client` object, it can call it by the name `module_01`.  If the NodeJS wrapper opens a second `ModuleClient` instance, it could assign it the name `module_02`, and the test code could use that name to disambiguate between the two client objects.

When the node.js wrapper app returns the PUT call, it returns status 200 to indicate success with a `connectionId` value in the return body that can be used in future calls into the node wrapper:
```
{
  "connectionId": "module_01"
}
```

Now, when the test code calls `module_client.send_event(sent_message)`, it results in a `PUT` operation to `/module/module_01/event/` with the contents of `sent_message` in the body of the request.

Finally, the call to `module_client.disconnect()` results in a `PUT` operation to `/module/module_01/disconnect`


## 2500 feet: the swagger file

All of this works because we have a standard REST api for all of our SDK wrappers.  This is defined in a swagger file that is specific to these tests. (We didn't want to other swagger definitions that the team is working on because we didn't want to be encumbered by the full set of features and we wanted to define our REST API based on our specific test requirements).

The swagger file that is truth is located in this repo as e2e_restapi.yaml.  Most of the language wrappers have a copy of the swagger file, but the truth is here.

For example, the subset of the swagger file that deals with connecting a module, sending telemetry, and disconnecting looks like this, with one REST function for each operation that the test code could execute.  

```
  /module/connectFromEnvironment/{transportType}:
    put:
      tags: ["module"]
      summary: Connect to the azure IoT Hub as a module using the environment variables
      parameters:
        - name: transportType
          in: path
          description: Transport to use
          required: true
          type: string
          enum: [amqp, amqpws, mqtt, mqttws, http]
      responses:
        200:
          description: OK
          schema:
            "$ref": "#/definitions/connectResponse"
  /module/{connectionId}/event:
    put:
      tags: ["module"]
      summary: Send an event
      consumes:
        - "text/json"
      parameters:
        - name: connectionId
          in: path
          description: Id for the connection
          required: true
          type: string
        - name: eventBody
          in: body
          required: true
          schema:
            type: string
      responses:
        200:
          description: OK
  /module/{connectionId}/disconnect:
    put:
      tags: ["module"]
      summary: Disconnect the module
      description: "Disconnects from Azure IoTHub service.  More specifically, closes all connections and cleans up all resources for the active connection"
      parameters:
        - name: connectionId
          in: path
          description: Id for the connection
          required: true
          type: string
      responses:
        200:
          description: OK
```

## 1000 feet: inside the wrapper app
Each SDK has their own wrapper app, and each wrapper app is based on on code that gets generated from tools published at http://swagger.io.  Because we're using REST for interop, that means that each wrapper app is running a RESTAPI server that exposes itself over some local port (usually 8080 or thereabouts).

| language | REST server | link |
|---|---|---|
| C | RestBed (C++) | https://github.com/Corvusoft/restbed |
| Node | | connect | https://www.npmjs.com/package/connect |
| Python | Flask | https://pypi.org/project/Flask/ |
| CSharp | aspnetcore | https://docs.microsoft.com/en-us/aspnet/core/?view=aspnetcore-2.1 |
| Java | vertx | https://vertx.io/ |


All of the wrapper apps look roughly like this:

```
+------------------------------------------------------+
| HTTP Server exposing REST endpoints                  |
+------------------------------------------------------+
+------------------------------------------------------+
| auto-generated wrappers                              |
| called controllers, api, and/or services             |
| depending on the language                            |
+------------------------------------------------------+
+------------------------------------------------------+
| "GLUE".  Hand written code that connects the         |
| generated code to our SDK                            |
+------------------------------------------------------+
+------------------------------------------------------+
| Language SDK                                         |
+------------------------------------------------------+
```

As a generalization, the functionality works like this:
* Layer 1: HTTP server.  This is the main app of the language wrapper.  It opens a port on some network endpoint (like 8080) and listens for incoming HTTP requests.  For each HTTP request it receives, it validates it against the swagger file.  If it looks correct, the server parses the parameters out of the request based on what is defined in the swagger.  It puts the parsed request into some sort of structure that is it's own native representation.
* Layer 2: Auto-generated wrappers.  This code takes the structure that the HTTP server produces, pulls out the specific parameters, and calls the next layer.  You can think of this like a dispatcher for HTTP requests.  It takes the request structure that is optimized for the HTTP server above and turns it into understandable function calls that are optimized for the layer below.
* Layer 3: Glue.  This code is written by and hand and has functions for each of the operations defined in the swagger file.  It calls into the specific language SDK to carry out the operation and it returns the result to the wrapper code above.
* Layer 4: Langauge SDK.  This is the code under test.  An individual HTTP server can (and usually does) host multiple SDKs.  For example, the C wrapper app links with the iothub device SDK and the iothub service SDK, with different REST endpoints interacting with different SDKs.

## 500 feet: REST endpoint organization

The REST endpoints that we test through are grouped by functionality based roughly on the API surface that is being tested.  The REST endpoints are prefixed with the surface name, and are marked with swagger tags so the code generator separates implementation by tag.  For example, all functions in the module client have an endpoint that beings with /module and are tagged with the word "module".  This tag allows the code generator to put the wrappers for module client functions into ModuleApi.cpp (for example), and we're able to easily map ModuleApi.cpp into ModuleGlue.cpp

The endpoint groups are as follows

| group | meaning |
|---|---|
| module | functions in the iothub moduleClient |
| registry | functions for the service SDK that interact with the iotHub registry |
| service | functions for the service SDK that interact with the iotHub serviceClient surface |
| device | functions in the iotHub deviceClient |
| wrapper | functions that are sort-of global to the test app.  A better name might have been "utility," but it's too late to change this now |
| eventhub | functions that expose Azure eventHub functionality |

Additionally, since moduleClient and deviceClient share a large amount of functionality, the wrappers that implement both likely have an internal glue file which acts like a base class for both the moduleGlue and deviceGlue implementations.

Caveat #1: Not all language wrappers have to implement all endpoint groups.  The test runner is written in such a way that a missing implementation in one SDK can be offloaded by the wrappers for a different SDK.  As an example, right now Node is the only wrapper that fully implements the deviceClient group, so tests which require an interaction between a module and a device (such as a module calling a direct method on a device), will run using the SDK under test (say, Java) for the moduleClient and the Node SDK for the deviceClient that it's calling into.  This allows us some flexibility in how much of an SDK surface we wrap for each DSK and it gives us the ability to test interactions between different language SDKs.  This way, we can verify that the structure that is passed by the Java SDK for a direct method call is able to be parsed by the Node SDK.

Caveat #2: The eventHub surface is only implemented by the node SDK and will probably never be implemented by any other SDK.  There is no reason to write wrappers for the eventHub SDK for every language that we test because we aren't responsible for those eventHub SDKs, so we don't have anything to gain by testing them all individually.  One implementation (node) is good enough.  The likely evolution is to move the /eventhub group out of the swagger file and implement the eventhub functionality directly in the test runner code.

# Pulling it all together: How do the tests flow?

Unlike typical E2E tests, the logic of the test does not live in the same process as the code that is being tested.  Because of this, it is not possible to simply launch a single executable to run through the tests.  The typical flow, which ignores the complexity of running inside iotEdge, testing multiple languages, or running inside a CI process goes like this:

1) The HTTP server that contains the language wrappers is launched somewhere.  In production, this might be inside of a docker container on an IoTEdge device.  During development, this might be inside of a debugger.
2) That HTTP server opens up a port and listens for REST calls from the test runner.  For every REST call it receives, it calls a single glue function and returns the result back over HTTP.
3) The glue function calls a single SDK operation passing the parameters that came over REST and returning the result without any analysis or judgement.
4) The test code that sent the REST request looks at the response and decides what to do next.

In this way, all of the logic that defines the _flow_ of the test is defined in the test runner.  The SDK wrappers are there to act like servants of the test runner, executing the functionality that the test runner specifies without knowing why it's doing what it's doing.  Likewise, the SDk wrappers are unable to know if an individual test has passed or failed because it is only returning the result of the operation to the test runner.  The test runner, as the owner of the flow of the test, is able to look at the results that are returned by the wrapper and determine if the test passed or not.

Another aspect of the flow is that each test case (for example `test_service_can_set_desired_properties_and_module_can_retrieve_them`), implements a full independent session with the SDKs that are being tested.  This means that the test creates both a moduleClient and a serviceClient object (through the SDK wrappers), connects both of them to their particular network destination (again, through the SDK wrapper), uses them to run the tests, and then disconnects the clients.  This is different than the typical lifetime of client objects, but still valid, and has the benefit of allowing us to pinpoint failures inside of shorter interactions.  If longer client lifetimes are desired in the future, longer tests can be written that keep client objects open for a longer time and perform multiple operations during the lifetime of the client objects.

Finally, each test case has beforeEach() and afterEach() code that verifies that all connections are closed, particularly in the case of failures that might leave connections open.  This is done to keep a clean environment, but it does not verify that nothing has leaked.  Additional leak verification between test cases can be added in the future.  It should be noted that this is a limitation of the language SDKs and not a limitation of the test architecture.  The wrapper group in each language SDK has a function that gets called before each test and after each test, and that wrapper for that SDK can decide what do inside those functions (such as checking for leaks).  Right now all wrappers are written to silently close all connections that might have accidentally been left open.  This was done with the assumption that any open connections are a result of failures that have already been reported, but this might not be the case.

