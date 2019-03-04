# Remote debugging C# containers

Since Horton runs (almost) all code that is being tested inside of Docker containers, it is useful to be able to remotely debug code that runs inside of containers.  This procedure specifically involves using a Windows install of Visual Studio Code to debug the C# wrapper inside of a Linux container.

## when is this useful?

This is useful for:
1. Catching exceptions inside of tests inside of debuggers
2. Tracing through C# SDK code or C# glue code

## A note on example output

* All PowerShell commands (with `PS` in the prompt) are run on your Windows box.
* All bash commands (with `bertk@bertk-newvm-1` in the prompt) are run on your Linux VM.
* All bash commands (with root and a hex number in the prompt -- like `root@63aafb3a5193:`) are run inside a docker container bash prompt.

## Step 1: configure your Windows machine to use SSH to connect to your container

### First, generate a public/private keypair if you haven't already.

If you already have keys (probably in `$env:USERPROFILE/.ssh/id_rsa` and `id_rsa.pub`), then you can skip this step.

**What this accomplishes**: This creates the encryption keys used to communicate between Visual Studio Code and the Docker container that is running the C# code.

**Command to run**: `ssh-keygen` (accept default values for all prompts)

**Example output**:
```
PS C:\WINDOWS\system32> ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (C:\Users\bertk/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in C:\Users\bertk/.ssh/id_rsa.
Your public key has been saved in C:\Users\bertk/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:bcNxD/Nf4Qk7TVbqxcJG3egjTbaXZOR2VEi+i/Ogu9o bertk@redmond@bertk
The key's randomart image is:
+---[RSA 2048]----+
|             .+=*|
|             +**+|
|          . +*OB=|
|         o o.B&==|
|        S =  +=*.|
|         . . ..o.|
|            + . .|
|         . . +   |
|        ..Eo  .  |
+----[SHA256]-----+
PS C:\WINDOWS\system32>
```
### Next, make sure the `ssh-agent` service is running

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

### Copy the public key into your clipboard

Because you want the `csharpMod` container to accept incoming SSH connections from your Windows box, you need to copy the public key you created above inside the docker container.

**What this accomplishes**: This gets the public key from your Windows box ready to paste into the container you want to debug.

**Commands to run**: `type C:\Users\bertk\.ssh\id_rsa.pub`, followed by copying the text -- the entire line starting with `ssh-rsa` and ending with your user and machine name (`bertk@redmond@bertk` in this example)

**Example output**:
```
PS C:\WINDOWS\system32> type C:\Users\bertk\.ssh\id_rsa.pub
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKsBUS1TRBvNrXYCVSPNUmQr2CmOsxTCA4Uvoe2L3RVvcQx8vcrM8hIy/XhBvzLQQcvuLJCg8V+/N566vh81uUbCL9qv7Bg/n/zWmEsRViAZ3LucSSCZy/3ywRDY33bcIwZ4TBS57irA/yn/FsytZmVO5yp53kS1CPHZEXwmn2GlO7eIY8DJ2oOgm8by2uip4qOW6zFOqgYQQxZ98bsmEgv7WZHVuPb1adW56B67zA1M28opSmbZyIc4xp71DKyAGHijxapM28eO6vFtxxMOvWYM072uQydTm9XtOQMc2vkRycDMRhFzr1VOd8PLiZj90WsGVQMg/tmyzNoXDVBdnD bertk@redmond@bertk
PS C:\WINDOWS\system32>
```
### Paste the public key into your docker container and start the `sshd` server

For this step, we're going to start at a vm bash prompt, then use `docker exec` to launch a bash prompt inside the docker container where we can paste that public key.

**What this accomplishes**: This tells the container to accept incoming SSH connections from your Windows box.

**Commands to run**:
* `docker exec -it csharpMod /bin/bash`
* `echo <KEY> >> /root/.ssh/authorized_keys`
* `service ssh start`
* `ps -auf`

**Example output**:
```
(Python-3.6.6) bertk@bertk-newvm-1:~$ docker exec -it csharpMod /bin/bash

root@63aafb3a5193:/app# echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDKsBUS1TRBvNrXYCVSPNUmQr2CmOsxTCA4Uvoe2L3RVvcQx8vcrM8hIy/XhBvzLQQcvuLJCg8V+/N566vh81uUbCL9qv7Bg/n/zWmEsRViAZ3LucSSCZy/3ywRDY33bcIwZ4TBS57irA/yn/FsytZmVO5yp53kS1CPHZEXwmn2GlO7eIY8DJ2oOgm8by2uip4qOW6zFOqgYQQxZ98bsmEgv7WZHVuPb1adW56B67zA1M28opSmbZyIc4xp71DKyAGHijxapM28eO6vFtxxMOvWYM072uQydTm9XtOQMc2vkRycDMRhFzr1VOd8PLiZj90WsGVQMg/tmyzNoXDVBdnD bertk@redmond@bertk" >> /root/.ssh/authorized_keys

root@63aafb3a5193:/app# service ssh restart
[ ok ] Restarting OpenBSD Secure Shell server: sshd.

root@63aafb3a5193:/app#
```

### Find the SSH port to use

**What this accomplishes**: Docker containers can map their SSH ports to different host ports, so we need know which port to use

**Command to run**: `docker ps`

In this example, I can see that `csharpMod` has port `22` in the container mapped to port `8183` on the linux VM, so `8183` is the number I will use as the SSH port in all the instructions to follow.  I got this from the part of the csharpMod line that said `0.0.0.0:8183->22/tcp`

**Example output**:
```
(Python-3.6.6) bertk@bertk-newvm-1:~$ docker ps
CONTAINER ID        IMAGE                                        COMMAND                   CREATED             STATUS              PORTS                                                                  NAMES
63aafb3a5193        localhost:5000/csharp-e2e-v2:latest          "dotnet IO.Swagger.d…"    19 hours ago        Up 19 hours         0.0.0.0:8183->22/tcp, 0.0.0.0:8083->80/tcp                             csharpMod
57b67a969d31        iotsdke2e.azurecr.io/edge-e2e-node6:latest   "/usr/local/bin/node…"    23 hours ago        Up 22 hours         9229/tcp, 0.0.0.0:8099->8080/tcp                                       friendMod
ac005d2e013f        mcr.microsoft.com/azureiotedge-hub:1.0.6     "/bin/sh -c 'echo \"$…"   2 days ago          Up 22 hours         0.0.0.0:443->443/tcp, 0.0.0.0:5671->5671/tcp, 0.0.0.0:8883->8883/tcp   edgeHub
6ea3dd7d1bc4        mcr.microsoft.com/azureiotedge-agent:1.0.6   "/bin/sh -c 'echo \"$…"   2 days ago          Up 22 hours                                                                                edgeAgent
fad673089b1f        registry:2                                   "/entrypoint.sh /etc…"    4 weeks ago         Up 4 days           0.0.0.0:5000->5000/tcp                                                 registry
(Python-3.6.6) bertk@bertk-newvm-1:~$
```

### Verify that you're able to connect from Windows into your container:

**What this accomplishes**: Before we get into configuring vscode to use the SSH connection, we want to make sure we can connect to the container by opening a bash shell remotely.

**command to run**: `ssh.exe -i $env:USERPROFILE/.ssh/id_rsa root@<YOUR_LINUX_VM> -p 8183`

**example output**:
```
PS C:\WINDOWS\system32> ssh.exe -i $env:USERPROFILE/.ssh/id_rsa root@bertk-newvm-1 -p 8183
The authenticity of host '[bertk-newvm-1]:8183 ([10.30.60.147]:8183)' can't be established.
ECDSA key fingerprint is SHA256:oTx2q1xyarXDSF3FX2mOk0qSoffF2ibVCN4HB7RU6PM.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '[bertk-newvm-1]:8183,[10.30.60.147]:8183' (ECDSA) to the list of known hosts.
Linux 63aafb3a5193 4.15.0-45-generic #48-Ubuntu SMP Tue Jan 29 16:28:13 UTC 2019 x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
root@63aafb3a5193:~#
```

**If you see an error `REMOTE HOST IDENTIFICATION HAS CHANGED!`**: You need to remove the previous ECDSA fingerprint for this container from your $env:USERPROFILE/.ssh/known_hosts file (or remove the file entirely to start over)


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
                "/wrapper": "HORTON_ROOT_PATH/ci_wrappers/csharp/wrapper",
                "/sdk": $(workspaceRoot)
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

**(one possible) command to use**: `pytest --csharp-wrapper -m testgroup_edgehub_module_client`

**Example output**:
```
(Python-3.6.6) bertk@bertk-newvm-1:~/repos/e2e-fx/test-runner$ pytest --csharp-wrapper -m testgroup_edgehub_module_client
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
