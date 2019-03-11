# Remote debugging C# containers

Since Horton runs (almost) all code that is being tested inside of Docker containers, it is useful to be able to remotely debug code that runs inside of containers.

This document includes instructions for setting up an SSH connection between a Windows machine and a container for the purpose of remote debugging.

## A note on example output

* All PowerShell commands (with `PS` in the prompt) are run on your Windows box.
* All bash commands (with `bertk@bertk-newvm-1` in the prompt) are run on your Linux VM.
* All bash commands (with root and a hex number in the prompt -- like `root@63aafb3a5193:`) are run inside a docker container bash prompt.

## Step 1: Make sure the `ssh-agent` service is running

In this step, we use an elevated powershell prompt to enable the `ssh-agent` service

**What this accomplishes**: The vscode extensions that we use to communicate with the docker container go over an SSH connection and we need the `ssh-agent` service to be running in order to use that connection.

**Commands to run**: `Set-Service ssh-agent -StartupType Automatic`, `Start-Service ssh-agent`, and `Get-Service ssh-agent` to validate that the service is running

**Example output**:
```
PS C:\WINDOWS\system32> Set-Service ssh-agent -StartupType Automatic
PS C:\WINDOWS\system32> Start-Service ssh-agent
PS C:\WINDOWS\system32> Get-Service ssh-agent

Status   Name               DisplayName
------   ----               -----------
Running  ssh-agent          OpenSSH Authentication Agent


PS C:\WINDOWS\system32>
```


## Step 2: Get source and connection credentials from your container
In this step, we extract the source, ssh key, and port from the running container.

**What this accomplishes**:

The source is necessary because your local clone of the SDK repo might not exactly match the code that was used to build the container image.  By using a copy of the source from the container, we can know that the code you're looking at inside the debugger is correct.

The ssh key and port are necessary because they give you credentials and a port for connecting to the SSH service inside the running container.

You need to do this after the container is deployed and running.

**Commands to run**: `./scripts/get-remote-source.sh csharp`

**Example output**:
```
(Python-3.6.6) bertk@bertk-newvm-1:~/repos/e2e-fx$ ./scripts/get-remote-source.sh csharp
running tests for for csharp
Copying source and ssh key for csharp into /home/bertk/repos/e2e-fx/csharp_source
Source for csharpMod is in /home/bertk/repos/e2e-fx/csharp_source

SSH key for csharpMod is in /home/bertk/repos/e2e-fx/csharp_source/remote-debug-ssh-key
csharpMod has ssh exposed on port 8183

to connect to csharpMod, call:
ssh -i /home/bertk/repos/e2e-fx/csharp_source/remote-debug-ssh-key root@bertk-newvm-1 -p 8183

Before using SSH, connect with docker exec:
docker exec -it csharpMod /bin/bash
Then restart the sshd service:
service ssh restart
```

You may get the following output if your container is not set up correctly (example for c sdk):

```
running tests for for c
Copying source and ssh key for c into /home/yoseph/GitRepos/iot-sdks-e2e-fx/c_source
Source for cMod is in /home/yoseph/GitRepos/iot-sdks-e2e-fx/c_source
Template parsing error: template: :1:3: executing "" at <index (index .Networ...>: error calling index: index of untyped nil
SSH port 22 is not exposed from cMod
```
This indicates you have not set up your container to open the SSH port 22.

## Step 3: connect to the container and restart the sshd service

**What this accomplishes**: For some unknown reason, sshd needs to be manually restarted before it will accept incoming connections.

**Commands to run**: `docker exec -it csharpMod /bin/bash` followed by `service ssh restart`

**Example output**:
```
(Python-3.6.6) bertk@bertk-newvm-1:~/repos/e2e-fx$ docker exec -it csharpMod /bin/bash
root@a534615ad920:/app# service ssh restart
[ ok ] Restarting OpenBSD Secure Shell server: sshd.
root@a534615ad920:/app# exit
exit
(Python-3.6.6) bertk@bertk-newvm-1:~/repos/e2e-fx
```

### Verify that you're able to connect from Windows into your container:
This step assumes that you've copied the remote-debug-ssh-key file from your linux VM to your windows machine.

**What this accomplishes**: Before we get into configuring vscode to use the SSH connection, we want to make sure we can connect to the container by opening a bash shell remotely.

**command to run**: `ssh.exe -i <LOCAL COPY OF KEY>@<YOUR_LINUX_VM> -p <SSH PORT>`

**example output**:
```
PS F:\temp\csharp_source> ssh.exe -i c:\Users\bertk\.ssh\remote-debug-ssh-key root@bertk-newvm-1 -p 8183
Linux a534615ad920 4.15.0-45-generic #48-Ubuntu SMP Tue Jan 29 16:28:13 UTC 2019 x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
root@a534615ad920:~#
```

**If you see an error `REMOTE HOST IDENTIFICATION HAS CHANGED!`**: You need to remove the previous ECDSA fingerprint for this container from your $env:USERPROFILE/.ssh/known_hosts file (or remove the file entirely to start over)

**If you see an error `Load key ".\\remote-debug-ssh-key": bad permissions`**: Move remote-debug-ssh-key into $env:USERPROFILE/.ssh/ and try again


**If it asks for a password for root**: Something in your parameters is wrong.  If you're correctly using the right key (from `id_rsa.pub`) to connect to the right host on the right port, then it shouldn't need to ask for a password.  You should verify that the right key is present in the location on the ssh.exe command line, then re-verify that the port is correct (using `docker ps` as outlined above) and finally verify that the host is correct.  If the name of the host looks correct, then try to ping your linux VM from your Windows box and make sure it works, which may involve comparing the IPV4 address for your linux VM is actually using with the IPV4 address that your Windows box is trying to use to connect to it.

## Step 2: Install VSCode prerequisites

Install the `ms-vscode.csharp` extension into vscode which will allow you to debug.

## Step 3: create VSCode debugger config to connect remotely
Inside VSCode, open `.vscode/launch.json` and add the following.  Replace the following values:
* `YOUR_VM_NAME`: This is the hostname for your VM
* `YOUR_CONTAINER_PORT`": This is the port you got from `docker ps` above (`8183` in my example)
* `HORTON_ROOT_PATH`: This is a pointer to your local copy of Horton so it can find the glue source files.

```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": ".NET Core Attach",
            "type": "coreclr",
            "request": "attach",
            "processId": "1",
            "pipeTransport": {
                "pipeProgram": "ssh",
                "pipeArgs": ["-T", "root@YOUR_VM_NAME", "-p", "YOUR_CONTAINER_PORT"],
                "debuggerPath": "/vsdbg/vsdbg",
            },
            "sourceFileMap": {
                "/wrapper": "PATH/csharp_source/wrapper",
                "/sdk": "PATH/csharp_source/sdk",
            }
        }
    ]
}
```


## Step 6: Attach your debugger to the container

In vscode, press F5 to start the debugger.  If it all works, you should start seeing debug output in the terminal at the bottom.

![cs-rd-03.png](\cs-remotedebug-assets\cs-rd-03.png)

## Step 7: Launch your tests

You probably do this using a bash prompt on your Linux VM.  As the test is running inside your bash window, you should see debug output in your vscode debugger window.  This is how you know it's running.

**(one possible) command to use**: `pytest --csharp-wrapper --scenario=edgehub_module_client`

**Example output**:
```
(Python-3.6.6) bertk@bertk-newvm-1:~/repos/e2e-fx/test-runner$ pytest --csharp-wrapper --scenario=edgehub_module_client
=================================== test session starts ===================================
platform linux -- Python 3.6.6, pytest-3.8.2, py-1.6.0, pluggy-0.8.1 -- /home/bertk/env/Python-3.6.6/bin/python3
cachedir: .pytest_cache
rootdir: /home/bertk/repos/e2e-fx/test-runner, inifile: pytest.ini
plugins: timeout-1.3.2, testdox-1.0.1, repeat-0.7.0, mock-1.10.0, cov-2.6.0, asyncio-0.10.0
timeout: 90.0s
timeout method: signal
timeout func_only: False
collecting 44 items
Using mqtt
Using csharp wrapper
```
