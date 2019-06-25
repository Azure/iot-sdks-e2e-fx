#!/usr/bin/env powershell
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
$root_dir = Join-Path -Path $path -ChildPath '../..' -Resolve
$scripts = Join-Path -Path $root_dir -ChildPath 'scripts' -Resolve
. $scripts/pwsh-helpers.ps1
$isWin32 = IsWin32

function CheckVerString([string] $pyVerStr) {

    $PyVer = $pyVerStr.Split('.')
    $PvMaj = [int]$PyVer[0]
    $PvMin = [int]$PyVer[1]

    if($PvMaj -gt $PythonMinVersionMajor)
    {
        Write-Host "Found Python Version: " $pyVerStr -ForegroundColor Green
        return $true
    }
    if($PvMaj -eq $PythonMinVersionMajor)
    {
        if($PvMin -ge $PythonMinVersionMinor)
        {
            Write-Host "Found Python Version: " $pyVerStr -ForegroundColor Green
            return $true
        }
    }
    return $false
}

function SearchForPythonVersion()
{
    Write-Host "Checking for python version (minimum): $PythonMinVersionMajor.$PythonMinVersionMinor" -ForegroundColor Yellow

    try {
        $PyVerCmd = & python3 -V 2>&1
        $PyParts = $PyVerCmd.split(' ')
        return CheckVerString($PyParts[1])
    }
    catch {
        try {
            $PyVerCmd = & python -V 2>&1
            $PyParts = $PyVerCmd.split(' ')
            return CheckVerString($PyParts[1])
        }
        catch {
            Write-Host "Continuing" -ForegroundColor Yellow
        }
    }
    
    $PyPath = Which("python")
    $pyVerFound = $false
    if ($PyPath) {
        foreach($PyFile in $PyPath)
        {
            try {
                $PyVer = (Get-Item $PyFile).VersionInfo
                $pyFound =  CheckVerString($PyVer.FileVersion)
                if($pyFound)
                {
                    Write-Host "Found: $PyFile" -ForegroundColor Green
                    $pyVerFound = $true
                }
            }
            catch {
                Write-Host "Continuing." -ForegroundColor Yellow
            }
        }
    }
    return $pyVerFound
}

function which([string]$cmd) {
    if($isWin32) {
        $cmd += '.exe'
    }
    Write-Host "Looking for $cmd in path..." -ForegroundColor Yellow
    try {
        $path = (Get-Command $cmd).Path
    }
    catch {
        $path = $null
    }
    if($null -eq $path) {
        Write-Host "Command $cmd NOT FOUND in path" -ForegroundColor Red
    }
    return $path
}

$PythonMinVersionMajor = 3
$PythonMinVersionMinor = 6
set-location $root_dir

$foundPy = SearchForPythonVersion($PythonMinVersionMajor, $PythonMinVersionMinor)
if($foundPy -ne $true)
{
    Write-Host "Python version not found" -ForegroundColor Red
    if ($isWin32) {
        Write-Host "Please install python 3.6 on Windows." -ForegroundColor Red
        exit 1
    }
    else {
            Write-Host "Installing python 3.6..." -ForegroundColor Yellow
            sudo apt-get install -y python3
    }
    if($LASTEXITCODE -eq 0) {
        Write-Host "python3 installed successfully" -ForegroundColor Green
    } 
    else {
        Write-Host "python3 install failed"  -ForegroundColor Red
        exit 1
    }
}

$gotPip3 = $false
$Pip3Path = Which("pip3")
if($null -ne $Pip3Path -and $Pip3Path.Length -lt 1)
{
    Write-Host "Pip3 not found" -ForegroundColor Red
    if($isWin32) {
        Write-Host "Installing pip3..." -ForegroundColor Yellow
        python -m ensurepip
    }
    else {
        Write-Host "Installing pip3..." -ForegroundColor Yellow
        sudo apt-get install -y python3-pip
    }
    if($LASTEXITCODE -eq 0) {
        Write-Host "pip3 installed successfully" -ForegroundColor Green
        $gotPip3 = $true
    } 
    else {
        Write-Host "pip3 install failed"  -ForegroundColor Red
        exit 1
    }
}

if($gotPip3) {
    Write-Host "Updating pip" -ForegroundColor Yellow
    Invoke-PyCmd "-m pip install --upgrade pip"

    if($LASTEXITCODE -eq 0) {
        Write-Host "pip updated successfully" -ForegroundColor Green
    } 
    else {
        Write-Host "pip update failed"  -ForegroundColor Red
        exit 1
    }
}

Write-Host "Installing python libraries" -ForegroundColor Yellow
set-location "$root_dir/ci-wrappers/pythonpreview/wrapper"
Invoke-PyCmd "-m pip install setuptools"
Invoke-PyCmd "-m pip install --user -e python_glue"
if($LASTEXITCODE -ne 0)
{
    Write-Host "user path not accepted.  Installing globally" -ForegroundColor Yellow
    Invoke-PyCmd "-m pip install -e python_glue"
    if($LASTEXITCODE -ne 0)
    {
        Write-Host "Install python_glue failed" -ForegroundColor Green
        exit 1
    } 
} 

Write-Host "Installing horton_helpers" -ForegroundColor Yellow
set-location $root_dir
Invoke-PyCmd "-m pip install --user -e horton_helpers"
if($LASTEXITCODE -ne 0)
{
    Write-Host "user path not accepted.  Installing globally" -ForegroundColor Yellow
    Invoke-PyCmd "-m pip install -e horton_helpers"
    if($LASTEXITCODE -ne 0) {
        Write-Host "install horton_helpers failed" -ForegroundColor Green
        exit 1
    } 
} 
else {
    Write-Host "horton_helpers installed successfully" -ForegroundColor Green
} 

Write-Host "Installing requirements for Horton test runner" -ForegroundColor Yellow
set-location $root_dir/test-runner
Invoke-PyCmd "-m pip install --user -r requirements.txt"
if($LASTEXITCODE -ne 0) {
    Write-Host "user path not accepted.  Installing globally" -ForegroundColor Yellow
    Invoke-PyCmd "-m pip install -r requirements.txt"
    if($LASTEXITCODE -ne 0) {
        Write-Host "install horton testrunner failed" -ForegroundColor Green
        exit 1
    } 
} 
else {
    Write-Host "horton testrunner installed successfully" -ForegroundColor Green
} 

Write-Host "Python3 and Python libraries installed successfully" -ForegroundColor Green
