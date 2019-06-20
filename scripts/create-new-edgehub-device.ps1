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
    $py = Run-PyCmd "-m pip install -e $hh"; Invoke-Expression $py
}

$py = Run-PyCmd "$pyscripts/create_new_edgehub_device.py"; Invoke-Expression $py

if($isWin32 -eq $false) {
    sudo systemctl restart iotedge
}
