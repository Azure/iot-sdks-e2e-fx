# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

Param
(
    [Parameter(Position=0)]
    [string]$test_scenario,

    [Parameter(Position=1)]
    [string]$test_transport,

    [Parameter(Position=2)]
    [string]$test_lang,

    [Parameter(Position=3)]
    [AllowEmptyString()]
    [string]$test_junitxml="",

    [Parameter(Position=4)]
    [AllowEmptyString()]
    [string]$test_o="",

    [Parameter(Position=5)]
    [AllowEmptyString()]
    [string]$test_extra_args=""
)

$path = $MyInvocation.MyCommand.Path
if (!$path) {$path = $psISE.CurrentFile.Fullpath}
if ( $path) {$path = split-path -Path $path -Parent}
Set-Location $path
. $path/pwsh-helpers.ps1
$isWin32 = IsWin32
$root_dir = Join-Path -Path $path -ChildPath '..' -Resolve
$testpath = Join-Path -Path $path -ChildPath '../test-runner' -Resolve

try {
    $cert_val = $env:IOTHUB_E2E_EDGEHUB_CA_CERT
    if("$cert_val" -ne "") {
        Write-Host "found IOTHUB_E2E_EDGEHUB_CA_CERT"
    }
}
catch {
    Write-Host "NOT found IOTHUB_E2E_EDGEHUB_CA_CERT"
}
set-location $root_dir/scripts
./get-environment.ps1

if($isWin32 -eq $false) {
    $EncodedText = sudo cat /var/lib/iotedge/hsm/certs/edge_owner_ca*.pem | base64 -w 0
    if( "$EncodedText" -ne "") {
        Set-Item -Path Env:IOTHUB_E2E_EDGEHUB_CA_CERT -Value $EncodedText
    }
}

$cert_val = $env:IOTHUB_E2E_EDGEHUB_CA_CERT
if("$cert_val" -ne "") {
    $cert_val = $cert_val.SubString(0,18)
    Write-Host "XOTHUB_E2E_EDGEHUB_CA_CERX($cert_val)" -ForegroundColor Red -BackgroundColor Yellow
}
else {
    Write-Host "(NULL) XOTHUB_E2E_EDGEHUB_CA_CERX" -ForegroundColor Red -BackgroundColor Yellow   
}

set-location $testpath
write-host "###### pytest -v --scenario $test_scenario --transport=$test_transport --$test_lang-wrapper --junitxml=$test_junitxml -o $test_o $test_extra_args"
if($isWin32) {
    python -u -m pytest -v --scenario $test_scenario --transport=$test_transport --$test_lang-wrapper --junitxml=$test_junitxml -o $test_o
}
else {
    sudo -H -E python3 -u -m pytest -v --scenario $test_scenario --transport=$test_transport --$test_lang-wrapper --junitxml=$test_junitxml -o $test_o $test_extra_args
}
