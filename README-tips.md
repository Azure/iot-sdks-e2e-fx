# Edge E2E tips and tricks

## Installing the Azure CLI
If you need to use the Azure CLI, I recommend using it in a docker container.
```
F:\repos\internals\edge-e2e\scripts>docker run --name azure-cli -it microsoft/azure-cli:2.0.24
bash-4.3#
```
Then, inside the container, add our extension, login, and set the subscription you want to use.
```
bash-4.3# az extension add --name azure-cli-iot-ext
bash-4.3# az login
To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code BXDB4Q6DM to authenticate.
[
{
<<<snip>>>
}
]
bash-4.3# az account set --subscription "Microsoft Azure IoT SDKs Development"
```

## tip: test discovery
1. pytest will look for tests in all .py files that start with 'test'. If you want to disable an entire file, rename it so it doesn't start with 'test'
2. inside test*.py files, pytest will run tests in any function with a name that starts with test. To remove an individual test, just rename the function.
3. To run an individual test, use filename::testname syntax to invoke pytest:
```
root@d67351a32694:/test-runner/tests# pytest test_module_twin_reported_properties.py::test_module_can_set_reported_properties_and_service_can_retrieve_them
```
4. To run a single file, pass the filename to pytest:
```
root@d67351a32694:/test-runner/tests# pytest test_module_twin_reported_properties.py
```

