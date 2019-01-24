# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
export IOTHUB_E2E_EDGEHUB_CA_CERT=$(sudo cat /var/lib/iotedge/hsm/certs/edge_owner_ca*.pem | base64 -w 0)
echo "To use this host to connect via connection string, set the following environment variable:"
echo "set IOTHUB_E2E_EDGEHUB_CA_CERT=${IOTHUB_E2E_EDGEHUB_CA_CERT}"
echo ""
echo "For the C# sdk, you should instead add this cert to your Trusted Root Certification Authorities node in the certificate store of your development machine"
sudo cat /var/lib/iotedge/hsm/certs/edge_owner_ca*.pem