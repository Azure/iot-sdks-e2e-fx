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
$root_dir = Join-Path -Path $path -ChildPath '..' -Resolve

Write-Host "Fetching Logs"

$log_folder_name = $log_folder_name.trim("/")
$resultsdir="$build_dir/results/logs/$log_folder_name"
$junit_file = "$build_dir/TEST-$log_folder_name.xml"

if( -Not (Test-Path -Path $resultsdir ) )
{
    New-Item -ItemType directory -Path $resultsdir
}
else {
    Get-ChildItem -Path "$resultsdir/*" -Recurse | Remove-Item -Force -Recurse
    Remove-Item -Path $resultsdir -Force -Recurse
    New-Item -ItemType directory -Path $resultsdir
}

$languageMod = $langmod + "Mod"
$modulefiles = @()
$modulelist = @( $languageMod, "friendMod", "edgeHub", "edgeAgent")
foreach($mod in $modulelist) {
    if("$mod" -ne "") {
        $modFile ="$resultsdir/$mod.log"
        $modulefiles += $modFile
        Write-Host "getting log for $mod" -ForegroundColor Green
        if($isWin32) {
            docker logs -t $mod  | Out-File $modFile
        }
        else {
            sudo docker logs -t $mod | Out-File $modFile
        }
    }
}

if($isWin32 -eq $false)  {
    $out = sudo journalctl -u iotedge -n 500 -e 2>&1
    $out  | Out-File $resultsdir/iotedged.log -Append
}

$arglist = ""
foreach($mod in $modulefiles) {
    $arglist += "-staticfile $mod "
}

Write-Host "merging logs for $modulelist" -ForegroundColor Green
$py = Run-PyCmd "${root_dir}/pyscripts/docker_log_processor.py $arglist > $resultsdir/merged.log"; Invoke-Expression  $py

Write-Host "injecting merged.log into junit" -ForegroundColor Green
$py = Run-PyCmd "${root_dir}/pyscripts/inject_into_junit.py -junit_file $junit_file -log_file $resultsdir/merged.log"; Invoke-Expression  $py

$files = Get-ChildItem "$build_dir/TEST_*"
if($files) {
    Move-Item $files "$build_dir/results/logs"
}
if(Test-Path -Path $junit_file )
{
    Copy-Item $junit_file -Destination "$build_dir/results/logs"
}
