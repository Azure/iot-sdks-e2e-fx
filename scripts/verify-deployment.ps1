# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

Param
(
    [Parameter(Position=0)]
    [AllowEmptyString()]
    [string]$container_name="",
    
    [Parameter(Position=1)]
    [AllowEmptyString()]
    [string]$image_name=""
)

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path $path -Parent}
. $path/pwsh-helpers.ps1
$isWin32 = IsWin32

if( "$container_name" -eq "" -or "$image_name" -eq "") {
    Write-Host "Usage: verify-deployment [container_name] [image_name]" -ForegroundColor Red
    Write-Host "eg: verify-deployment nodeMod localhost:5000/node-test-image:latest" -ForegroundColor Red
    exit 1
}

$expectedImg = ""
$actualImg = ""
$expectedImg = ""
$running = $true
$out_progress = "."
$expectedImg = ""

if($isWin32) {
    $container_name = $container_name.ToLower()
    $image_name = $image_name.ToLower()
}
Write-Host "getting image ID for Image:($image_name) Container:($container_name)" -ForegroundColor Green

foreach($i in 1..37) {
    if("$out_progress" -eq ".") {
        Write-Host "calling docker inspect ($image_name)" -ForegroundColor Green
    }

    if($isWin32) {
        $expectedImg = docker image inspect $image_name --format="{{.Id}}"
    }
    else {
        $expectedImg = sudo docker image inspect $image_name --format="{{.Id}}"
    }

    if("$expectedImg" -ne "") {
        #Write-Host "Got ImageId for ($image_name)=($expectedImg)" -ForegroundColor Blue
        Write-Host "Inspecting Image ($container_name) for .State.Running" -ForegroundColor Green
        if($isWin32) {
            $running = docker image inspect --format="{{.State.Running}}" $container_name 
        }
        else {
            $running = sudo docker inspect --format="{{.State.Running}}" $container_name
        }
        #Write-Host "Container ($container_name) running = ($running)" -ForegroundColor Magenta
        if($running) {
            Write-Host "Container is running.  Checking image" -ForegroundColor Green

            if($isWin32) {
                $actualImg = docker inspect $container_name --format="{{.Image}}"
            }
            else {
                $actualImg = sudo docker inspect $container_name --format="{{.Image}}"
            }
            #Write-Host "Actual ImageId: ($actualImg)" -ForegroundColor Green
            if($expectedImg -eq $actualImg) {
                Write-Host "IDs match.  Deployment is complete"  -ForegroundColor Green
                exit 0
            }
            else {
                Write-Host "container is not running.  Waiting"  -ForegroundColor Yellow
            }
        }
    }
    Write-Host "$out_progress" -ForegroundColor Blue
    $out_progress += "."
    Start-Sleep -s 10    
}

exit 1
