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
$tryresultsdir="$build_dir/results/logs/$log_folder_name"
$junit_file = "$build_dir/$log_folder_name.xml"

if( -Not (Test-Path -Path $tryresultsdir ) )
{
    New-Item -ItemType directory -Path $tryresultsdir
}
else {
    Get-ChildItem -Path "$tryresultsdir/*" -Recurse | Remove-Item -Force -Recurse
    Remove-Item -Path $tryresultsdir -Force -Recurse
    New-Item -ItemType directory -Path $tryresultsdir
}
$resultsdir = $tryresultsdir

$stdout = @()
$stderr = @()
$got_mods = @()
$languageMod = $langmod + "Mod"
$modulelist = @( $languageMod, "friendMod", "edgeHub", "edgeAgent")
foreach($mod in $modulelist) {
    if("$mod" -ne "") {
        Write-Host "getting log for $mod" -ForegroundColor Green
        try {
            if($isWin32) {
                $stdout = docker logs -t $mod 2>($tmpFile=New-TemporaryFile)
                $stderr = Get-Content $tmpFile; Remove-Item $tmpFile
            }
            else {
                $stdout = sudo docker logs -t $mod 2>($tmpFile=New-TemporaryFile)
                $stderr = Get-Content $tmpFile; Remove-Item $tmpFile
            }
            $got_mods += $mod
        }
        catch {
            Write-Host "Exception getting log for $mod" -ForegroundColor Red
            $_
        }
        if("$stderr" -ne "") {
            $stdout | Out-File $resultsdir/$mod.log -Append
            foreach($o in $stderr) {
                Write-Host $o -ForegroundColor Red
            }
        }
        if("$stdout" -ne "") {
            foreach($o in $stderr) {
                $o | Out-File $resultsdir/$mod.log -Append
            }
        }
    }
}

if($isWin32 -eq $false)  {
    $out = sudo journalctl -u iotedge -n 500 -e 2>&1
    $out  | Out-File $resultsdir/iotedged.log -Append
}

$arglist = ""
$modlist = ""
foreach($mod in $modulelist) {
    if("$mod" -ne "") {
        if($mod -contains $got_mods) {
            $arglist += "-staticfile $resultsdir/$mod.log "
            $modlist += "$mod "
        }
    }
}

set-location $resultsdir
$out = @()
Write-Host "merging logs for $modlist" -ForegroundColor Green

$py = Run-PyCmd "${root_dir}/pyscripts/docker_log_processor.py $arglist"; $out = Invoke-Expression  $py

if ($LASTEXITCODE -ne 0) {
    Write-Host "error merging logs" -ForegroundColor Red
    foreach($o in $out) {
        Write-Host $o
    }
}
else {
    $out | Out-File $resultsdir/merged.log
}

set-location $resultsdir
Write-Host "injecting merged.log into junit" -ForegroundColor Green

$py = Run-PyCmd "${root_dir}/pyscripts/inject_into_junit.py -junit_file $junit_file -log_file $resultsdir/merged.log"; $out = Invoke-Expression  $py
foreach($o in $out) {
    Write-Host $o -ForegroundColor Yellow
}

#$files = Get-ChildItem "$build_dir/TEST-*" | Where-Object { !$_.PSIsContainer }
$files = Get-ChildItem "$build_dir/TEST-*"
if($files) {
    Move-Item $files "$build_dir/results/logs"
}
