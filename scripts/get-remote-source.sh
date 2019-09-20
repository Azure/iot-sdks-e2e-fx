# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

language=$1
case "$language" in
  node | pythonv1 | c | csharp | java | pythonv2)
    echo "running tests for for $language"
    ;;
  *)
    echo "Usage: $0 [node | pythonv1 | c | csharp | java | pythonv2]"
    exit 1
    ;;
esac

module=${language}Mod
status=$(docker inspect --format='{{.State.Status}}' $module)
if [ $? -ne 0 ] || [ $status != "running" ]; then
    echo $module is not running
    exit 1
fi

dest=$(pwd)/${language}_source

mkdir $dest

echo "Copying source and ssh key for $language into $dest"

docker cp $module:/sdk $dest/sdk
[ $? -eq 0 ] || { echo "failed copying sdk from container"; exit 1; }

docker cp $module:/wrapper $dest/wrapper
[ $? -eq 0 ] || { echo "failed copying wrapper from container"; exit 1; }

echo Source for $module is in $dest

port=$(docker inspect --format='{{(index (index .NetworkSettings.Ports "22/tcp") 0).HostPort}}' $module)
if [ $? -ne 0 ]; then
    echo "SSH port 22 is not exposed from $module"
else
    docker cp $module:/root/.ssh/remote-debug $dest/remote-debug-ssh-key
    [ $? -eq 0 ] || { echo "failed copying ssh key from container"; exit 1; }

    echo ""
    echo "SSH key for $module is in $dest/remote-debug-ssh-key"
    echo "$module has ssh exposed on port $port"
    echo ""
    echo "to connect to $module, call:"
    echo "ssh -i ${dest}/remote-debug-ssh-key root@$(hostname) -p $port"
    echo ""
    echo "Before using SSH, connect with docker exec:"
    echo "docker exec -it $module /bin/bash"
    echo "Then restart the sshd service:"
    echo "service ssh restart"
fi

