# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import os


class Container:
    """
    The Container object contains all of the details about an implementation of our test objects running inside of a Docker container. It contains:
    * Information which is typically static, such as the Docker image for the LKG implementation of the code.
    * Information which can change at runtime, such as the Docker image to be used for this particular run of the tests.
    * Information about the capabilities of the test container, such as "does this container implement the DeviceClient API?"
    * Information needed to deploy the container to an iotEdge instance, such as the container port (which is the port number that is exposed in the container's port space) and the host port (which is mapped by Docker into localhost's port space)
    *
    * The intention of this object is to encapsulate any information which might change from container to container.
    """

    def __init__(self):
        self.name = ""
        self.module_id = ""
        self.lkg_image = ""
        self.image_to_deploy = ""
        self.container_port = 0
        self.host_port = 0
        self.local_port = 0
        self.add_routes = True
        self.serviceImpl = True
        self.registryImpl = True
        self.deviceImpl = True
        self.connection_string = ""
        self.required = False


all_containers = {}

node = Container()
node.name = "node"
node.module_id = "nodeMod"
node.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-node6:latest"
node.host_port = 8080
node.container_port = 8080
node.local_port = 8080
all_containers["node"] = node

friend = Container()
friend.name = "friend"
friend.module_id = "friendMod"
friend.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-node6:latest"
friend.container_port = 8080
friend.host_port = 8099
friend.local_port = 8080
friend.add_routes = False
friend.required = True
all_containers["friend"] = friend

python = Container()
python.name = "python"
python.module_id = "pythonMod"
python.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-python36:latest"
python.container_port = 8080
python.host_port = 8081
python.local_port = 8080
python.serviceImpl = False
python.registryImpl = False
python.deviceImpl = False
all_containers["python"] = python

c = Container()
c.name = "c"
c.module_id = "cMod"
c.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-gcc:latest"
c.container_port = 8082
c.host_port = 8082
c.local_port = 8082
c.deviceImpl = False
all_containers["c"] = c

csharp = Container()
csharp.name = "csharp"
csharp.module_id = "csharpMod"
csharp.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-csharp:latest"
csharp.container_port = 80
csharp.host_port = 8083
csharp.local_port = 50352
csharp.deviceImpl = False
all_containers["csharp"] = csharp

java = Container()
java.name = "java"
java.module_id = "javaMod"
java.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-java8:latest"
java.container_port = 8080
java.host_port = 8084
java.local_port = 8080
java.deviceImpl = False
all_containers["java"] = java

pythonpreview = Container()
pythonpreview.name = "pythonpreview"
pythonpreview.module_id = "pythonpreviewMod"
pythonpreview.lkg_image = (
    os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/edge-e2e-pythonpreview:latest"
)
pythonpreview.container_port = 8080
pythonpreview.host_port = 8085
pythonpreview.local_port = 8080
pythonpreview.serviceImpl = False
pythonpreview.registryImpl = False
pythonpreview.deviceImpl = False
all_containers["pythonpreview"] = pythonpreview
