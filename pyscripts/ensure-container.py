# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import docker
import argparse
import requests
import sys
import time

containerMap = {
  'nodeMod':  8080,
  'pythonMod': 8081,
  'cMod': 8082,
  'csharpMod': 8083,
  'javaMod': 8084,
  'pythonpreviewMod': 8085,
  'friendMod': 8099,
}

parser = argparse.ArgumentParser(description="ensure that a test container is running.  Restart the container if it does not respond.")
parser.add_argument("container_name", help="container to validate", type=str, choices=containerMap.keys())
args = parser.parse_args()

container_name = args.container_name
port = containerMap[container_name]
client = docker.from_env()

try:
  container = client.containers.get(container_name)
except docker.errors.NotFound:
  print("Container {} is not deployed".format(container_name))
  sys.exit(1)

restart_attempts = 10
container_startup_time = 5

for f in range(0, restart_attempts):
  try:
    r = requests.put("http://localhost:{}/wrapper/message".format(port), json={"msg": "test message from ensure_container.py"})
  except Exception as e:
    print("Container {} is not responding".format(container_name))
    print(str(e))
  else:
    print("Container {} is running and responding".format(container_name))
    sys.exit(0)

  print("restarting container {}".format(container_name))
  container.restart()

  time.sleep(container_startup_time)

print("Container {} did not respond after {} restart attempts".format(container_name, restart_attempts))
sys.exit(1)







