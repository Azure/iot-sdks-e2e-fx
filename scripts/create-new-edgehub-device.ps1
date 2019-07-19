#!/usr/bin/env pwsh
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1
$isWin32 = IsWin32
$pyscripts = Join-Path -Path $path -ChildPath '../pyscripts' -Resolve

Invoke-PyCmd "$pyscripts/create_new_edgehub_device.py"

if($isWin32 -eq $false) {
    sudo systemctl restart iotedge
}
