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
$resultsdir="$build_dir/results/logs/$log_folder_name"
$junit_file = "$build_dir/TEST-$log_folder_name.xml"

Write-Host "Fetching Logs for $log_folder_name" -ForegroundColor Green
$ErrorActionPreference = "SilentlyContinue"
if( -Not (Test-Path -Path $resultsdir ) )
{
    New-Item -ItemType directory -Path $resultsdir
}
else {
    Get-ChildItem -Path "$resultsdir/*" -Recurse | Remove-Item -Force -Recurse
    Remove-Item -Path $resultsdir -Force -Recurse
    New-Item -ItemType directory -Path $resultsdir
    #mkdir $resultsdir >$null
}

Write-Host "#######################################"
docker container ls
Write-Host "#######################################"

set-location $resultsdir
$languageMod = $langmod + "Mod"
$modulefiles = @()
$dkr_log = @()
$dlen = 0
$modulelist = @( $languageMod, "friendMod", "edgeHub", "edgeAgent")
foreach($mod in $modulelist) {
    if("$mod" -ne "") {
        $modFile ="$resultsdir/$mod.log"
        $modulefiles += $modFile
        #if(Test-Path $modFile) {
        #    Remove-Item $modFile
        #}
        Write-Host "Getting log for $mod" -ForegroundColor Green
        #$dkr_log = Invoke-Cmd "sudo docker logs -t $mod"
        #Invoke-Cmd "docker logs -t $mod"
        #$dkr_log = Invoke-Expression "sudo docker logs -t $mod" 4>&1 >> $modFile
        if($isWin32)  {
            $dkr_cmd = "docker logs -t $mod"
        }
        else {
            $dkr_cmd = "sudo docker logs -t $mod 4>&1"
        }
        #$dkr_cmd = "docker image ls"
        #$dkr_log = Invoke-Expression $dkr_cmd 
        Invoke-Expression $dkr_cmd | Out-File $modFile
        #Get-Content -Path $modFile | Measure-Object -Line
        Write-Host "#######################################"
        Get-Content -Path $modFile
        #$dkr_log = ( Invoke-Expression $dkr_cmd ) | Out-File $modFile
        #$dlen = $dkr_log.length
        #Write-Host "($modFile)($dlen)"
        #$dkr_log | Out-File $modFile
        #foreach( $o in $dkr_log) {
            #$o >> $modFile
        #    Write-Host "__$o"
        #}
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
#$py = Run-PyCmd "${root_dir}/pyscripts/docker_log_processor.py $arglist"; Invoke-Expression "& '$py' > $resultsdir/merged.log"
#$py = Run-PyCmd "${root_dir}/pyscripts/docker_log_processor.py $arglist"; $out_log = (Invoke-Expression $py)
$py = Run-PyCmd "${root_dir}/pyscripts/docker_log_processor.py $arglist"; Invoke-Expression $py | Out-File $resultsdir/merged.log
#$out_log > $resultsdir/merged.log
#| Out-File $modFile
#$out_log | Out-File $resultsdir/merged.log -Append

Write-Host "injecting merged.log into junit" -ForegroundColor Green

$py = Run-PyCmd "${root_dir}/pyscripts/inject_into_junit.py -junit_file $junit_file -log_file $resultsdir/merged.log"; Invoke-Expression $py
#$py = Run-PyCmd "${root_dir}/pyscripts/inject_into_junit.py -junit_file $junit_file -log_file $resultsdir/merged2.log"; Invoke-Expression $py

$files = Get-ChildItem "$build_dir/TEST_*"
if($files) {
    Move-Item $files "$build_dir/results/logs"
}
if(Test-Path -Path $junit_file )
{
    Copy-Item $junit_file -Destination "$build_dir/results/logs"
}
