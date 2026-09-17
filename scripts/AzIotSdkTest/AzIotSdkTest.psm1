# Azure IoT SDK end-to-end test framework.
#
# The loader is a .ps1 rather than inline here so that the deprecated
# scripts/Azure.Iot.Sdk.Test.psm1 shim can dot-source the SAME loader: PowerShell's
# dot-source operator only accepts .ps1, and a shim that used Import-Module instead
# would export its commands from a differently-named module.
. (Join-Path $PSScriptRoot 'Import-Parts.ps1')
