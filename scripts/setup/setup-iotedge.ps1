# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
$root_dir = Join-Path -Path $path -ChildPath '../..' -Resolve
$scripts = Join-Path -Path $root_dir -ChildPath 'scripts' -Resolve
. $scripts/pwsh-helpers.ps1
$isWin32 = IsWin32

if($isWin32 -eq $false) {
    Write-Host "Installing iotedge..." -ForegroundColor Yellow
    sudo apt-get install -y iotedge
    sudo chmod 666 /etc/iotedge/config.yaml
}
