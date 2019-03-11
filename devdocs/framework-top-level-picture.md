# Top Level Picture for the Horton Test Framework

This document is a broad outline of the problems we are solving now, the problems we are not trying to solve, and the problems we want to solve in the future.

## Framework goal, scope and status

This section outlines some of the significant factors that affect the entire test framework.  This includes the primary goals, non-goals, and some status

### Test all SDKs

We're building a single framework that can test all of the Azure IoT SDKs with a minimum of language-specific code.  We want to re-use as much of the test collateral across languages as possible.

### Focus on IoT Edge modules, cover IoT Hub modules

Our primary driver, at least to start, is IoT Edge modules.  Coverage for IoT Hub modules is secondary, as they support a subset of IoT Edge module features.

### Currently Linux only, Windows soon

Until recently, we've been focusing our efforts on testing under Linux.  We're now expanding this into Windows and raspberry pi.

### Focus on fast turnaround

We want to use this in a CI/CD environment, so we obviously want fast test runs.  Speed is largely accomplished by two thins:
1) Smart use of Docker image layering and caching
2) Running suites in parallel on multiple build agents.

Current run time is between 8 and 20 minutes for a single language with all transports.  The `docker build` step is the biggest cause of variation here.  (We leverage docker image caching as much as possible, but bigger changes might require more layers in the container to be rebuilt).

### Start with simple tests to get 100% coverage, then increase complexity as needed

We're currently focusing on simple scenarios and building up successful test passes across all languages with all transports.  Once we have a reliable baseline established, we can incrementally increase coverage and complexity.

### Use Azure DevOps for execution

We're using Azure DevOps pipelines as the primary way to run test passes.  More specifically, we want to use Microsoft-hosted agents for running all of our test jobs.  This means that we want to limit the pre-allocated resources as much as possible, and script so resources get created as needed, within reason.

Running individual tests and entire suites on developer workstations is also a goal.  The scripts that run entire matrices of suites are limited to running on Azure DevOps machines.

### Primarily for gating and CI/CD

These tests are written primarily to validate the Azure IoT SDKs.  Our future direction includes plans to eventually use this framework as a means to validate IoT Edge releases and Azure service deployments.

### Includes fault-injection tests

This framework is also being leveraged to do fault-injection testing.  This is currently limited to IoT Edge connections using the MQTT protocol with the C sdk, and we are actively working to increase the coverage.

## Future direction

Development on this framework is active and ongoing.  This section outlines a few of the future plans

### IoT Edge validation jobs

Writing jobs to validate IoT Edge releases is largely a matter of scripting the installers to use private binaries instead of public ones.  With this, and with coordination with the Edge team, this tool could be used to validate Edge releases.

### More environments

The jobs we run use one primary environment per language.  We want to expand coverage, both in terms of OS (or container base image), language versions, and built tools.

### Tiered matrices

Since we have one environment per language, we can easily run all scenarios on every commit.  As we add more environments, this will no longer be possible.  Because of this, we want to offer tiered matrices, so there's a limited set of tests on every commit, a larger set of tests on a longer schedule (from once-per-day to once-per-week), and a comprehensive set of tests once every release.  The intention here is to test all functionality on every commit, and use the bigger matrices to test on a wider set of environments.

### Running on dogfood, canary, and production

We currently run against production servers.  Expanding this to dogfood and canary is simply a matter of scripting the jobs to accept different connection strings.  This is made easy by the fact that there are no pre-allocated resources with the exception of the IoT Hub instance that we use to test.

### Non-edge cases (pnp, streaming, python-preview SDK)

We are evolving this framework so we efficiently cover more scenarios.  The python-preview SDK is an early adopter as they are hoping to use this framework for all of their E2E testing.