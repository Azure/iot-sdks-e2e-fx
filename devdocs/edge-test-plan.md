# IoT Edge Test Plan using the Horton Test Framework

This document is an outline of the specific test scenarios we are covering with the IoT Edge tests.

## Related documents

* For a big-picture of the Horton test framework, look [here](.\framework_top_level_picture.md)
* Some definitions useful in understanding the Horton framework are outlined [here](.\framework_definitions.md)
* Examples and visualizations for understanding the definitions are provided [here](.\framework_definitions_visualized.md)

## Definitions

In addition to the definitions used by the Horton framework, the following definitions are useful in describing the Edge E2E tests.
* __test module__ - This is the Edge Module, living inside a docker container, which contains the code that we are testing.
* __friend module__ - This is a secondary Edge module which is used to help validate the test module.  The friend module is used:
    * as a destination for output events that the test module sends
    * as a source for input messages that the test module receives
    * as a receiver for method calls that the test module invokes
    * as an invoker for method calls that the test module receives
* __leaf device__ - This is a limited Azure IoT Device client which is also used to help validate the test module.  The leaf device is used:
    * as a receiver for method calls that the test module invokes

The following names are also known, but they are part of a implementation details that are being phased out.
* __nodeMod__, __cMod__, __csharpMod__, __javaMod__, __pythonMod__, and __pythonPreviewMod__ - these are the names of docker containers that are used as test modules for different langauges.
* __friendMod__ - this is the name of the docker container which is responsible for acting as:
    * The friend module as defined above.
    * The leaf device as defined above.
    * a default implementation of the Service and Registry APIs, in case the module under test does not have an implementation to use for testing.

The fact that friendMod is an Edge module, and also a leaf device and an implementation of other APIs is confusing and should not be dwelt on as these pieces of functionality are eventually moving into their own containers

## Test Environments

## Test Suites (or "the matrix of suites")

## Test Cases

## Current Exclusions

## Current Pass Rates


