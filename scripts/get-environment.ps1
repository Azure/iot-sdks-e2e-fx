# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1
$isWin32 = IsWin32
$root_dir = Join-Path -Path $path -ChildPath '..' -Resolve
$pyscripts = Join-Path -Path $root_dir -ChildPath '/pyscripts' -Resolve

$edge_cert = "$env:IOTHUB_E2E_EDGEHUB_CA_CERT"

if($isWin32 -eq $false) {
    $EncodedText = sudo -H -E  cat /var/lib/iotedge/hsm/certs/edge_owner_ca*.pem | base64 -w 0
    if( "$EncodedText" -ne "") {
        Set-Item -Path Env:IOTHUB_E2E_EDGEHUB_CA_CERT -Value $EncodedText
    
    }
}

# force re-fetch of the device ID
#unset IOTHUB_E2E_EDGEHUB_DEVICE_ID
if( "$env:IOTHUB_E2E_EDGEHUB_CA_CERT" -eq "") {
    Write-Host "ERROR: IOTHUB_E2E_EDGEHUB_CA_CERT not set" -ForegroundColor Red
}
else {
    Remove-Item Env:IOTHUB_E2E_EDGEHUB_CA_CERT
}

$out = @()
$py = PyCmd-Run "$pyscripts/get_environment_variables.py powershell"; $out = Invoke-Expression  $py

foreach($o in $out) {
    $var_name,$var_value = $o.split('=')
    if("env:$var_name" -eq "") {
        Write-Host "Setting: $o" -ForegroundColor Magenta
        Set-Item -Path Env:$var_name -Value $var_value
    }
}

if("$env:IOTHUB_E2E_EDGEHUB_CA_CERT" -eq "") {
    Write-Host "Reverting to previous IOTHUB_E2E_EDGEHUB_CA_CERT" -ForegroundColor Red
    Set-Item -Path Env:IOTHUB_E2E_EDGEHUB_CA_CERT -Value $edge_cert
}
