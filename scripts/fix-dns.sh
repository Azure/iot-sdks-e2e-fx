# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

# install resolvconf package
which resolvconf
if [ $? -eq 0 ]; then
  echo "resolvconf package already exists.  skipping install"
else 
  sudo apt-get install -y resolvconf
  [ $? -eq 0 ] || { echo "apt-get install resolvconf failed"; exit 1; }
fi

new_dns="10.221.226.12 157.54.14.146 157.54.14.178"

added=
for ip in $new_dns; do
  grep $ip /etc/resolvconf/resolv.conf.d/head
  if [ $? -ne 0 ]; then
    echo "adding $ip to nameserver list"
    sudo bash -c "echo nameserver $ip >> /etc/resolvconf/resolv.conf.d/head"
    added=true
  fi
done

if [ $added ]; then
  echo "Items added to nameserver list.  running resolvconf -u"
  sudo resolvconf -u
else 
  echo "Nameserver list looks complete.  Nothing to do"
fi

