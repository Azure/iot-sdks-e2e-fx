# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1
$pyscripts = Join-Path -Path $path -ChildPath '../pyscripts' -Resolve

$py = Run-PyCmd "$pyscripts/remove_edgehub_device.py"; Invoke-Expression  $py
