# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

Param
(
    [Parameter(Position=0)]
    [string]$langmod,
    [Parameter(Position=1)]
    [string]$build_dir,
    [Parameter(Position=2)]
    [string]$log_folder_name
)

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1

$isWin32 = IsWin32

$log_folder_name = $log_folder_name.trim("/")
$root_dir = Join-Path -Path $path -ChildPath '..' -Resolve
$pyscripts = Join-Path -Path $root_dir -ChildPath 'pyscripts' -Resolve
$resultsdir="$build_dir/results/logs"

Write-Host "Fetching Logs for $log_folder_name in: $build_dir" -ForegroundColor Green

if(Test-Path -Path $resultsdir)
{
    Get-ChildItem -Path "$resultsdir/*" -Recurse | Remove-Item -Force -Recurse
    Remove-Item -Path $resultsdir -Force -Recurse
    New-Item -ItemType directory -Path $resultsdir
}
New-Item -ItemType directory -Path $resultsdir

$languageMod = $langmod + "Mod"
$modulefiles = @()
$modulelist = @( $languageMod, "friendMod", "edgeHub", "edgeAgent")
foreach($mod in $modulelist) {
    if("$mod.strip()" -ne "") {
        $modFile ="$resultsdir/$mod.log"
        $modulefiles += $modFile
        Write-Host "Getting log for $mod" -ForegroundColor Green
        Invoke-PyCmd "$pyscripts/get_container_log.py --container $mod" | Set-Content -Path $modFile
    }
}

if($isWin32 -eq $false)  {
    sudo journalctl -u iotedge -n 500 -e >$resultsdir/iotedged.log
}

Write-Host "merging logs for ($modulelist)" -ForegroundColor Green
$arglist = ""
foreach($modFile in $modulefiles) {
    if(Test-Path $modFile) {
        $arglist += "-staticfile $modFile "
    }   
}
Invoke-PyCmd "$pyscripts/docker_log_processor.py $arglist" | Set-Content -Path "$resultsdir/merged.log"

$junit_file = "$build_dir/TEST-$log_folder_name.xml"
Write-Host "injecting merged.log into junit: $junit_file" -ForegroundColor Green
Invoke-PyCmd "$pyscripts/inject_into_junit.py -junit_file $junit_file -log_file $resultsdir/merged.log"

New-Item -ItemType directory -Path $build_dir/results/$log_folder_name
Move-Item "$resultsdir/*" $build_dir/results/$log_folder_name
$files = Get-ChildItem "$build_dir/TEST_*"
if($files) {
    Move-Item $files "$build_dir/results"
}
if(Test-Path -Path $junit_file )
{
    Move-Item $junit_file -Destination "$build_dir/results"
}
