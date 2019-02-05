# What's the deal with ...

This document is where you look when you look when you find part of the code that makes you go "hmmmm...".

If you find something strange that you don't understand, feel free to add it here.

## steps-ensure-e2e-repo.yaml

It might seem strange to have a step to clone a repo from a pipeline step inside the repo, and it is.  This step is necessary becaues the pipeline YAML files are referenced from language SDK repositories.  It make sure there is a local copy of the e2e-fx repo on the pipeline machine so that yaml scripts can call into the various tools in this repo.

## ensure-container.py

Some of our containers, for some unknown reason, display the following error at startup:
```
sudo: unable to resolve host fv-az396
```
This is a problem with dsn resolution which prevents the container from knowing the ip address of the host.  It was previously thought to be a problem with BbusyBox containers, but it has also been seen on Alpine containers.  In the interest of stabalizing the SDK code as soon as possible, we are working around this by making sure the hosted containers respond to simple REST calls.  If the container does not respond, then we restart the container. 


