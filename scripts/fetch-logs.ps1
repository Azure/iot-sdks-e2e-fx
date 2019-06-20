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

Write-Host "---Fetching Logs"
$ErrorActionPreference = "SilentlyContinue"

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
    New-Item -ItemType directory -Path $resultsdir >$null
}

$languageMod = $langmod + "Mod"
$modulefiles = @()
$modulelist = @( $languageMod, "friendMod", "edgeHub", "edgeAgent")
foreach($mod in $modulelist) {
    if("$mod" -ne "") {
        $modFile ="$resultsdir/$mod.log"
        $modulefiles += $modFile
        Write-Host "Getting log for $mod" -ForegroundColor Green
        #$dkr_out = ""
        #"& 'c:\program files\7-zip\7z.exe' >xxx.txt"
        $dkr_out = Invoke-Expression "& 'sudo docker logs -t $mod' > $modFile"
        $dkr_out | Out-Null
#        if($isWin32) {
#            $out = Invoke-Expression "docker logs -t $mod > $modFile"
#        }
#        else {
#            $out = Invoke-Expression "sudo docker logs -t $mod > $modFile"
#        }
    }
}

if($isWin32 -eq $false)  {
    sudo journalctl -u iotedge -n 500 -e >$resultsdir/iotedged.log
}

Write-Host "merging logs for ($modulelist)" -ForegroundColor Green
$arglist = ""
foreach($mod in $modulefiles) {
    $arglist += "-staticfile $mod "
}
$py = Run-PyCmd "${root_dir}/pyscripts/docker_log_processor.py $arglist >$resultsdir/merged.log"; Invoke-Expression  $py

Write-Host "injecting merged.log into junit" -ForegroundColor Green
set-location $resultsdir
$py = Run-PyCmd "${root_dir}/pyscripts/inject_into_junit.py -junit_file $junit_file -log_file $resultsdir/merged.log"; Invoke-Expression  $py

$files = Get-ChildItem "$build_dir/TEST_*"
if($files) {
    Move-Item $files "$build_dir/results/logs"
}
if(Test-Path -Path $junit_file )
{
    Copy-Item $junit_file -Destination "$build_dir/results/logs"
}
