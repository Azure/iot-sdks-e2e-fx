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
node.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/node-e2e-v3:lkg"
node.host_port = 8080
node.container_port = 8080
node.local_port = 8080
all_containers["node"] = node

friend = Container()
friend.name = "friend"
friend.module_id = "friendMod"
friend.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/default-friend-module:latest"
friend.container_port = 8080
friend.host_port = 8099
friend.local_port = 8080
friend.add_routes = False
friend.required = True
all_containers["friend"] = friend

pythonv1 = Container()
pythonv1.name = "pythonv1"
pythonv1.module_id = "pythonv1Mod"
pythonv1.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/pythonv1-e2e-v3:lkg"
pythonv1.container_port = 8080
pythonv1.host_port = 8081
pythonv1.local_port = 8080
pythonv1.serviceImpl = False
pythonv1.registryImpl = False
pythonv1.deviceImpl = False
all_containers["pythonv1"] = pythonv1

c = Container()
c.name = "c"
c.module_id = "cMod"
c.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/c-e2e-v3:lkg"
c.container_port = 8082
c.host_port = 8082
c.local_port = 8082
c.deviceImpl = False
all_containers["c"] = c

csharp = Container()
csharp.name = "csharp"
csharp.module_id = "csharpMod"
csharp.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/csharp-e2e-v3:lkg"
csharp.container_port = 80
csharp.host_port = 8083
csharp.local_port = 50352
csharp.deviceImpl = False
all_containers["csharp"] = csharp

java = Container()
java.name = "java"
java.module_id = "javaMod"
java.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/java-e2e-v3:lkg"
java.container_port = 8080
java.host_port = 8084
java.local_port = 8080
java.deviceImpl = False
all_containers["java"] = java

pythonv2 = Container()
pythonv2.name = "pythonv2"
pythonv2.module_id = "pythonv2Mod"
pythonv2.lkg_image = os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/pythonv2-e2e-v3:lkg"
pythonv2.container_port = 8080
pythonv2.host_port = 8085
pythonv2.local_port = 8080
pythonv2.serviceImpl = False
pythonv2.registryImpl = False
pythonv2.deviceImpl = False
all_containers["pythonv2"] = pythonv2
