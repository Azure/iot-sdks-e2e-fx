# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
echo "WARNING: This action can not be undone!"
echo "Do you wish to completely remove iotedge from your machine?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

sudo apt purge -y libiothsm-std
sudo rm -r /var/run/iotedge/
sudo rm -r /var/lib/iotedge/

echo "done"