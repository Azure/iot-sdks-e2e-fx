#!/usr/bin/env powershell
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: Tag-DockerImage.ps1
# author:   v-greach@microsoft.com
# created:  03/11/2019
# Rev: 03/11/2019 C

Param
(
    [Parameter(Position=0)]
    [string]$Repository,
    [Parameter(Position=1)]
    [string]$TAG_OLD,
    [Parameter(Position=2)]
    [string]$TAG_NEW
)

$EnvRepo = $Env:IOTHUB_E2E_REPO_ADDRESS
$UserName = $Env:IOTHUB_E2E_REPO_USER
$Password   = $Env:IOTHUB_E2E_REPO_PASSWORD
$Registry = "https://" + $EnvRepo

if($Repository -eq "" -or
    $TAG_OLD -eq "" -or
    $TAG_NEW -eq "" -or
    $EvnRepo -eq "" -or
    $UserName -eq "" -or
    $Password -eq "") {
        Write-Output "ERROR- Missing parameter or environment variable"
        Write-Output "Usage:"
        Write-Output "    Tag-DockerImage <Repository> <CurrentTag> <NewTag>"
        Write-Output "Additionally these environment variables must be set:"
        Write-Output "IOTHUB_E2E_REPO_ADDRESS, IOTHUB_E2E_REPO_USER, IOTHUB_E2E_REPO_PASSWORD"
        exit
    }

$ContentType = 'application/vnd.docker.distribution.manifest.v2+json'

$Params = @{
    UseBasicParsing = $true
    Method          = 'Get'
    Uri             = "$Registry/v2/$Repository/manifests/$TAG_OLD"
    Headers         = @{
        Accept      = $ContentType
    }
}

$pair = "$($UserName):$($Password)"
$encodedCredentials = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($Pair))
$Params.Headers.Add('Authorization', "Basic $encodedCredentials")

try {
    $Response = Invoke-WebRequest @Params
    $Manifest = ConvertFrom-ByteArray -Data $Response.Content -Encoding ASCII
}
catch {
    Write-Output $Error[0]
}

$Params = @{
    UseBasicParsing    = $true
    Method             = 'Put'
    Uri                = "$Registry/v2/$Repository/manifests/$TAG_NEW"
    Headers            = @{
        'Content-Type' = $ContentType
    }
    Body               = $Manifest
}
$Params.Headers.Add('Authorization', "Basic $encodedCredentials")

try {
    $Response = Invoke-WebRequest @Params
    $RespCode = $Response.StatusCode
    if($RespCode -eq 201) {
        Write-Output "SUCCESS: Created new tag:$TAG_NEW from:$TAG_OLD in:$Repository"
    } else {
        Write-Output "FAILED: Status:$RespCode Creating new tag:$TAG_NEW from:$TAG_OLD in:$Repository"
    }
}
catch {
    Write-Output $Error[0]
}
