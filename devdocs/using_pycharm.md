# Goal
This document outlines how to configure PyCharm to debug the Horton test framework.  It is based on some personal preferences and outlines _one_ option for setting this up.

# My situation

* I'm  setting up PyCharm  (2018.3.4 Community Edition) on a Ubuntu 18.04 VM
* I like using virtual environments, created with pyenv.
* My fingers are used to Visual Studio shortcuts.
* I want to run/debug the tests in this repository with the PyCharm interface.
* I've been debugging in this repository with different tools, so I already have my VM and bash environments configured.  This means that I have docker containers for edgeHub, edgeAgent, friendMod, and my test module running, and I have my 4 IOTHUB_E2E_* environment variables set (IOTHUB_E2E_CONNECTION_STRING, IOTHUB_E2E_REPO_ADDRESS, IOTHUB_E2E_REPO_PASSWORD, and IOTHUB_E2E_REPO_USER)

![pc-01.png](\pycharm-assets\pc-01.png)

# Keymaps for Visual Studio

* This part is easy.  After launching PyCharm, select `File`->`Settings`->`Keymap`. Select `Visual Studio` in the dropdown.

![pc-02.png](\pycharm-assets\pc-02.png)

# Create the PyCharm project

* Create the pycharm project by opening the folder with your clone of this repo.

![pc-03.png](\pycharm-assets\pc-03.png)

* It should open PyCharm with the root of this repo as a Project

![pc-04.png](\pycharm-assets\pc-04.png)

# Optional: create a virtual environment for your project

* Select `File`->`Settings`->`Project <name>`->`Project Interpreter`.  If you're happy with the interpreter you're using, click OK.

![pc-05.png](\pycharm-assets\pc-05.png)

If you want to create a new virtual environment:
* Click the gear icon in the upper right of this dialog and select `Add`
* Select `New environment`.
* Change the `Location` to a folder outside the clone of the repo (to keep git happy)
* Pick a `Base interpreter` that you want to base your virtual environment from.

![pc-06.png](\pycharm-assets\pc-06.png)

* Click `OK`.  It will create the new environment.
* Make sure the environment you just created is selected in the "Project Interpreters" dialog and click "OK".
* Click "OK" again to close the settings dialog

![pc-07.png](\pycharm-assets\pc-07.png)

# pip install libraries in your environment.

* In the main PyCharm window, expand "External Libraries", then expand your environment, and verify that some set of libraries is showing up.  Any libraries installed by pip will show up under the "site packages" node.

![pc-08.png](\pycharm-assets\pc-08.png)

* To install libraries, open a bash prompt.  If you have a virtual environment, use the `source` command to activate it.

```
bertk@bertk-newvm-1:~$ source ~/pycharm-venv/bin/activate
(pycharm-venv) bertk@bertk-newvm-1:~$
```

* Then use `pip install` to install the libraries
```
(pycharm-venv) bertk@bertk-newvm-1:~$ cd repos/e2e-fx/test-runner/
(pycharm-venv) bertk@bertk-newvm-1:~/repos/e2e-fx/test-runner$ pip install -r requirements.txt
```

* Install any other libraries you might need (e.g. if you're using the python-preview repo with direct adapters, you need to run `env_setup.py` from that repo).
* If you close and re-open the PyCharm app, you should see all the libraries listed under site-packages

![pc-09.png](\pycharm-assets\pc-09.png)

# Create a Configuration for debugging your project
* With the project open in PyCharm, select `Run`->`Edit Configurations`
* Click the + button to add a new configuration.
* Select `Python tests`->`pytest`

![pc-10.png](\pycharm-assets\pc-10.png)

* In the new configuration page, select `custom`
* Set `Additional Arguments` to anything you need to pass to pytest.  (I use `--node-wrapper --scenario=iothub_module_client` for testing node iothub modules
* Set `Working Directory` to the `test-runner` folder.
* Click `OK`

![pc-11.png](\pycharm-assets\pc-11.png)

# Copy your environment into the pycharm `Run/Debug configuration`

* Exit the PyCharm app.
* In a bash prompt, run `scripts/get-environment.sh pycharm`.  It will ask for your password.  Enter it.

```
(pycharm-venv) bertk@bertk-newvm-1:~/repos/e2e-fx$ ./scripts/get-environment.sh pycharm
[sudo] password for bertk:
        <env name="IOTHUB_E2E_CONNECTION_STRING" value="REDACTED" />
        <env name="IOTHUB_E2E_EDGEHUB_DNS_NAME" value="bertk-newvm-1" />
        <env name="IOTHUB_E2E_EDGEHUB_DEVICE_ID" value="bertk-newvm-1_bertk_28405466" />
        <env name="IOTHUB_E2E_REPO_ADDRESS" value="REDACTED" />
        <env name="IOTHUB_E2E_EDGEHUB_CA_CERT" value="REDACTED" />
(pycharm-venv) bertk@bertk-newvm-1:~/repos/e2e-fx$
```

* Copy these values into your clipboard
* Use your favorite editor to open `.idea/workspace.xml`
* Copy these values inside an `envs` block under the node named ` <component name="RunManager">` and save.

```
  <component name="RunManager">
    <configuration name="pytest" type="tests" factoryName="py.test" nameIsGenerated="true">
      <module name="e2e-fx" />
      <option name="INTERPRETER_OPTIONS" value="" />
      <option name="PARENT_ENVS" value="true" />
      <envs>
        <env name="IOTHUB_E2E_CONNECTION_STRING" value="REDACTED" />
        <env name="IOTHUB_E2E_EDGEHUB_DNS_NAME" value="bertk-newvm-1" />
        <env name="IOTHUB_E2E_EDGEHUB_DEVICE_ID" value="bertk-newvm-1_bertk_28405466" />
        <env name="IOTHUB_E2E_REPO_ADDRESS" value="REDACTED" />
        <env name="IOTHUB_E2E_EDGEHUB_CA_CERT" value="REDACTED" />
      </envs>
      <option name="SDK_HOME" value="$USER_HOME$/pycharm-venv/bin/python" />
```

* To verify that this works, open PyCharm, select `Run`->`Edit Configurations`.  You should see these values in the `Environment variables` field, and you should be able to click the little folder icon to see the individual values

![pc-12.png](\pycharm-assets\pc-12.png)

# Finally, run the tests

* Inside PyCharm, select `Run`->`Run pytest` to run the tests.  You should see the tests running in the console window.
* When the tests are done running, you should see some tests pass.  You can ignore `Failed to start` -- this is not an error.  These are tests that are skipped.

![pc-13.png](\pycharm-assets\pc-13.png)
