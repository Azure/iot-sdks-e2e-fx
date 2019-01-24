# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

CONTAINERNAME=$1
if [ -z ${CONTAINERNAME} ]; then
  echo "usage: $0 [containername]"
  exit 1
fi

for i in {1..40}; do
  echo "calling \"docker inspect $CONTAINERNAME\""
  RUNNING=$(sudo docker inspect --format="{{.State.Running}}" $CONTAINERNAME)
  if [ $? -eq 0 ] && [ "$RUNNING" = "true" ]; then
    echo "container running. Restart $CONTAINERNAME complete"
    exit 0
  fi

  echo "container not running.  sleeping for 10 seconds."
  sleep 10
done

echo "container $CONTAINERNAME failed to start"
exit 1


