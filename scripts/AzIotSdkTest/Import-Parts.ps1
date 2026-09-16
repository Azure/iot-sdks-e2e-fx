# Loads the module parts, in order, into the scope of whatever dot-sources this
# file, and declares the public surface.
#
# Dot-sourced by AzIotSdkTest.psm1 (the real module) and by the deprecated
# scripts/Azure.Iot.Sdk.Test.psm1 shim, so both export the same commands.
#
# The order is explicit and NOT derived from the directory listing: PowerShell
# resolves a class used as a parameter type when the file declaring the consumer
# is parsed, so Models.ps1 must load before anything taking a
# [TestEnvironmentInfo]. Re-ordering these silently breaks the module.
#
# Adding a part means adding it to $ModuleParts. tests/Validate-Module.ps1 fails
# the build if a file in parts/ is missing from this list, which would otherwise
# leave it quietly unloaded.

[TimeSpan]$DefaultCertificateExpiration = [TimeSpan]::FromDays(365)

$ModuleParts = @(
    'Common.ps1'             # Logging, process invocation, temp files, error handling
    'AzureCommon.ps1'        # az CLI extension, retries, role assignments, resource groups
    'Conversion.ps1'         # Hashtable/PSObject conversion helpers
    'Crypto.ps1'             # Keys, CSRs, certificates, PEM
    'Models.ps1'             # Classes describing an provisioned test environment
    'Dps.ps1'                # DPS enrollment helpers
    'ResourceGroups.ps1'     # Resource group naming and leftover cleanup
    'Provisioning.ps1'       # New-/Get-AzIotTestEnvironment
    'TestConfig.ps1'         # Per-SDK test config emitters
    'SubmoduleGraph.ps1'     # Test-SubmoduleConsistency and its GitHub helpers
)

foreach ($ModulePart in $ModuleParts) {
    . (Join-Path (Join-Path $PSScriptRoot 'parts') $ModulePart)
}

Export-ModuleMember -Function Debug-PSScript
Export-ModuleMember -Function Invoke-Script
Export-ModuleMember -Function Set-FileContent
Export-ModuleMember -Function Get-AzureResourceGroupNamePrefix
Export-ModuleMember -Function New-AzureResourceGroupName
Export-ModuleMember -Function Remove-LeftoverAzureResourceGroups
Export-ModuleMember -Function New-AzIotTestEnvironment
Export-ModuleMember -Function Get-AzIotTestEnvironment
Export-ModuleMember -Function ConvertFrom-JsonToTestEnvironmentInfo
Export-ModuleMember -Function New-AzIotCSDKE2ETestConfig
Export-ModuleMember -Function New-AzIotNetSDKE2ETestConfig
Export-ModuleMember -Function New-AzIotPythonSDKE2ETestConfig
Export-ModuleMember -Function New-AzIotPythonSdkSampleConfig
Export-ModuleMember -Function New-AzIotuAmqpE2ETestConfig
Export-ModuleMember -Function New-AzIotHortonTestConfig
Export-ModuleMember -Function Test-SubmoduleConsistency
