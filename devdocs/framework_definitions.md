 # Definitions used commonly in the Horton test framework

While many of these words are overused and overloaded, they have specific definitions in the context of this framework.  All of these definitions are directly or indirectly coded into the current framework.  Other definitions for future framework direction are located in the future direction document.

* __Horton__ - Horton is the name of this test framework

## Defining Tests

* __test language__ - A test language is synonymous with an SDK repo.  For example, the framework currently has one language (`python`) which uses the old boost-based Python SDK, and a different language (`pythonpreview`) which uses the new native Python SDK.

* __test environment__ - A test environment is an amalgamation of operating system, language version, and build tools that a suite can run inside.  "ubuntu python 3.6" might be one environment, while "windows python 2.7" might be another.  Since we use containerized runtimes, the environment might also include details on the container definition, such as "Node 7 Alpine" or "C clang Stretch-slim".  A test environment only supports a single test langauge.

* __test case__ - A test case is an individual test with an easy one-sentence description.  e.g. "module calls direct method on another module".

* __test group__ - A test group is a set of test cases that, together, validate a single feature.  For example: `edge_module` is the group of test cases that run using the Module Client against IoT Edge, and hub_module is the (overlapping) group of test cases that run using the Module Client against IoT Hub.

* __test suite__ - A test group combined with some limited connection/execution parameters.  An example test group would be `edge_module_mqtt`.  This group runs runs the tests in the `edge_module` group using the `mqtt` transport.  This suite also has an implied connection parameter which causes the framework to use a GatewayHostName value to route through an EdgeHub instance.  Additionally, a suite implies some set of deployment instructions.  For example, a edge_module suite would imply deployment of the test code using an IoT Edge deployment, while a hub_module suite would imply a deployment using the docker engine directly.

* __test matrix__ - A test matrix is a set of test suites run on one or more environments.  Some matrices are single-environment (such as running all edgehub tests for all transports in a single environment), and other matrices are multi-environment (such as running all tests in a group of transports, so that each language is represented at least once).

* __test deployment__ - A test deployment defines a set of code installed into a particular environment.  The deployment contains (or implies) a set of Azure resources (such as connection strings or device IDs) necessary to run the tests

## Implementing Tests

* __API__ - An API is a language-independent abstraction of an SDK API (e.g. ModuleApi).  The API needs to define an interface which can be implemented in any langauge.  APIs are primarily implemented using REST, so they need to follow REST conventions and not expose any language dependent features (such as callbacks or coroutines)

* __adapter__ - An adapter defines an interop method for calling language-dependent wrappers from the langauge-independent test cases.  Currently most wrappers use REST for interop, though we have adapters to run Python wrappers in-proc.  Someday, other wrappers will be written to do interop over other channels (such as serial ports or named pipes).

* __language wrapper__ -  A language wrapper is an implementation of an API interface in a particular language.  For example, there is a Node language wrapper for the module API and also a csharp language wrapper for the same API.  Both wrappers expose the same REST interface and the same test code can operate against both wrappers.

* __glue__ - Glue code connects the langauge-independent API with an SDK.  For example, the Node wrapper contains Module Api glue.  This glue is called by the Node.JS rest server and, in turn, it calls the node.js sdk to implement the API functions.

## Running Tests

* __pipeline__ - Our test execution currently relies on Azure DevOps for execution.  The test execution, as defined in Azure DevOps, is a set of Jobs (each of which runs on it's own VM instance), and each job consists of a set of tasks (such as running `pip install` or pulling a docker container).  The group of jobs that we execute is implemented as an Azure DevOps Pipeline.

* __forced image__ - All of our test pipelines begin by building a docker image for a given environment with code that needs to be tested.  A forced image is a way to run a test pipeline with a docker image from a previous run.  This is typically done either to save execution time (by bypassing the `docker build` command), or to run a test pipeline with an SDK as it existed in the past (to help find the cause of a particular regression.)
