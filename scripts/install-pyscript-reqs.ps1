#!/usr/bin/env pwsh
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1
$root_dir = Join-Path -Path $path -ChildPath '..' -Resolve
$pyscripts = Join-Path -Path $root_dir -ChildPath 'pyscripts' -Resolve

Invoke-PyCmd "-m pip install --upgrade pip"
Invoke-PyCmd "-m pip install -r $pyscripts/requirements.txt"
