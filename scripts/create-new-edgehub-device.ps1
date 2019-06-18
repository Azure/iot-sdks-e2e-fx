# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1
$isWin32 = IsWin32
$pyscripts = Join-Path -Path $path -ChildPath '../pyscripts' -Resolve
$hh = Join-Path -Path $path -ChildPath '../horton_helpers' -Resolve

if($isWin32 -eq $false) {
    $py = PyCmd-Run "-m pip install -e $hh"; Invoke-Expression  $py
}

$out = @()
$py = PyCmd-Run "$pyscripts/create_new_edgehub_device.py"; $out = Invoke-Expression  $py
foreach($o in $out) {
    Write-Host $o
}

if($isWin32 -eq $false) {
    sudo systemctl restart iotedge
}
else {
    $devTag = "new edgeHub device created with device_id="
    $devTagLen = $devTag.Length
    $deviceName = ""
    foreach($o in $out) {
        $devNamePos = $o.IndexOf($devTag)
        if($devNamePos -ge 0) {
            $oLen = $o.Length
            $startPos = $devNamePos + $devTagLen
            $strSize = $oLen - ($devNamePos + $devTagLen)
            $deviceName = $o.Substring($startPos, $strSize)
            if( "$deviceName" -ne "") {
                break
            }
        }
    }
    if( "$deviceName" -ne "") {
        Write-Host "Setting IOTHUB_E2E_EDGEHUB_DEVICE_ID=$deviceName" -ForegroundColor Yellow
        Set-Item -Path Env:IOTHUB_E2E_EDGEHUB_DEVICE_ID -Value $deviceName    }    
}
