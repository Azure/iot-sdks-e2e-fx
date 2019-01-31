# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

CONTAINERNAME=$1
IMAGENAME=$2

if [ -z ${CONTAINERNAME} ] ||
   [ -z ${IMAGENAME} ]; then
  echo "usage: $0 [containername] [imagename]"
  echo "eg: $0 nodeMod localhost:5000/node-test-image:latest"
  exit 1
fi

# each iteration = ~ 10 seconds
for i in {1..24}; do
  echo "getting image ID for $IMAGENAME"
  EXPECTED_IMAGE_ID=$(sudo docker image inspect $IMAGENAME --format="{{.Id}}")
  if [ $? -eq 0 ]; then
    echo "expected image ID is $EXPECTED_IMAGE_ID"

    echo "calling \"docker inspect $CONTAINERNAME\""
    RUNNING=$(sudo docker inspect --format="{{.State.Running}}" $CONTAINERNAME)
    if [ $? -eq 0 ] && [ "$RUNNING" = "true" ]; then
      echo "Container is running.  Checking image"

      ACTUAL_IMAGE_ID=$(sudo docker inspect $CONTAINERNAME --format="{{.Image}}")
      [ $? -eq 0 ] || { echo "docker inspect failed"; exit 1; }
      echo "actual image ID is $ACTUAL_IMAGE_ID"

      if [ $EXPECTED_IMAGE_ID = $ACTUAL_IMAGE_ID ]; then
        echo "ID's match.  Deployment is complete"
        exit 0
      else
        echo "no match.  waiting"
      fi
    else
      echo "container is not running.  Waiting"
    fi
  else
    print "container is unkonwn.  Waiting."
  fi
  sleep 10
done

echo "container $CONTAINERNAME deployment failed"
exit 1


