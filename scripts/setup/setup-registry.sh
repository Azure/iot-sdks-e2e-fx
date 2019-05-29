# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

sudo docker inspect registry --format "{{.State.Status}}"
if [ $? -eq 0 ]; then
  echo "registry is already running"
else
  sudo docker run -d -p 5000:5000 --restart=always --name registry registry:2
  [ $? -eq 0 ] || { echo "docker run failed"; exit 1; }
fi

