# DEPRECATED PATH -- kept so that pipelines importing this file keep working.
#
# The module now lives in AzIotSdkTest/ next to this file, split into parts.
# This shim exists for the one consumption pattern that cannot see those files:
# a pipeline that downloads THIS SINGLE FILE from raw.githubusercontent.com and
# imports it.
#
# Prefer either of the acquisition paths that bring the whole repository, which
# pin the module to the same ref as the caller and need no download step:
#
#   GitHub Actions:  - uses: Azure/iot-sdks-e2e-fx/actions/provision-e2e-resources@<tag>
#   Azure Pipelines: resources.repositories + `- template: ...@e2e_fx`
#
# This file will be removed once the remaining raw-URL consumers have moved.

$ErrorActionPreference = 'Stop'

$PackageRoot = Join-Path $PSScriptRoot 'AzIotSdkTest'
$PackageLoader = Join-Path $PackageRoot 'Import-Parts.ps1'

if (Test-Path $PackageLoader) {
    # Normal case: this file is in a checkout, so the module is right here.
    # Dot-sourcing (rather than Import-Module) runs the real root module in THIS
    # module's scope, so its Export-ModuleMember calls export from this module
    # and the caller sees exactly the same commands as before.
    . $PackageLoader
    return
}

# Downloaded standalone. Fetch the package and dot-source it from there.
#
# Ref resolution, in order:
#   1. $env:AZ_IOT_SDK_TEST_REF, for a caller that wants a specific ref
#   2. the default below
#
# The default is 'master', which is what the existing raw-URL consumers already
# get today. It is NOT a good default -- it means a merge here changes their
# next run -- and is kept only so this shim is a drop-in replacement. Pin a tag.
$DefaultRef = 'master'

$Ref = if ($env:AZ_IOT_SDK_TEST_REF) { $env:AZ_IOT_SDK_TEST_REF } else { $DefaultRef }

Write-Warning "Azure.Iot.Sdk.Test.psm1 was imported without its package; downloading iot-sdks-e2e-fx@$Ref. Pin a tag and import AzIotSdkTest/AzIotSdkTest.psd1 from a checkout instead."

# Windows PowerShell 5.1 still defaults to TLS 1.0/1.1 on some hosts.
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch {
    Write-Verbose "Could not raise the TLS version: $($_.Exception.Message)"
}

$StagingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("AzIotSdkTest-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $StagingRoot -Force | Out-Null

try {
    $ZipPath = Join-Path $StagingRoot 'package.zip'
    $ZipUri = "https://github.com/Azure/iot-sdks-e2e-fx/archive/$Ref.zip"

    Invoke-WebRequest -Uri $ZipUri -OutFile $ZipPath -UseBasicParsing
    Expand-Archive -Path $ZipPath -DestinationPath $StagingRoot -Force

    $Downloaded = Get-ChildItem -Path $StagingRoot -Recurse -Filter 'Import-Parts.ps1' |
        Select-Object -First 1

    if (-not $Downloaded) {
        throw "iot-sdks-e2e-fx@$Ref does not contain scripts/AzIotSdkTest/Import-Parts.ps1."
    }

    # Dot-sourcing reads and parses the files now, so nothing under $StagingRoot
    # is needed once this returns and the directory can go.
    . $Downloaded.FullName
} finally {
    # Build agents are often persistent, and a failed download would otherwise
    # leave a partial copy behind on every run.
    Remove-Item -Path $StagingRoot -Recurse -Force -ErrorAction SilentlyContinue
}
