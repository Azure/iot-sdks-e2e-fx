# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

echo "clearing docker logs"
sudo sh -c "truncate -s 0 /var/lib/docker/containers/*/*-json.log" 
[ $? -eq 0 ] || { echo "failure clearing docker logs"; exit 1; }
exit 0

