<#
.SYNOPSIS
Checks the AzIotSdkTest module without provisioning anything.

.DESCRIPTION
The module is consumed by pipelines in other repositories, where a load-order or
export mistake only surfaces as a failed provisioning job. These checks are
cheap, need no Azure credentials, and run identically here and in CI:

  * every file under parts/ parses
  * the dot-source order in Import-Parts.ps1 lists every file in parts/, and
    lists nothing that is missing -- a part left out of the list loads silently
    as nothing at all
  * the module imports, and exports EXACTLY the expected commands: the list
    below is the module's public contract and consumers in other repositories
    call these by name
  * the manifest's FunctionsToExport agrees with what the module exports
  * the deprecated scripts/Azure.Iot.Sdk.Test.psm1 shim still yields the same
    commands when imported from a checkout

.EXAMPLE
pwsh -NoProfile -File tests/Validate-Module.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ScriptsRoot = Join-Path $RepoRoot 'scripts'
$PackageRoot = Join-Path $ScriptsRoot 'AzIotSdkTest'
$LoaderPath = Join-Path $PackageRoot 'Import-Parts.ps1'
$ManifestPath = Join-Path $PackageRoot 'AzIotSdkTest.psd1'
$ShimPath = Join-Path $ScriptsRoot 'Azure.Iot.Sdk.Test.psm1'
$PartsRoot = Join-Path $PackageRoot 'parts'

# The module's public contract. Changing this list changes what other
# repositories can call, so it is spelled out here rather than derived.
$ExpectedExports = @(
    'ConvertFrom-JsonToTestEnvironmentInfo'
    'Debug-PSScript'
    'Get-AzIotTestEnvironment'
    'Get-AzureResourceGroupNamePrefix'
    'Invoke-Script'
    'New-AzIotCSDKE2ETestConfig'
    'New-AzIotHortonTestConfig'
    'New-AzIotNetSDKE2ETestConfig'
    'New-AzIotPythonSDKE2ETestConfig'
    'New-AzIotPythonSdkSampleConfig'
    'New-AzIotTestEnvironment'
    'New-AzIotuAmqpE2ETestConfig'
    'New-AzureResourceGroupName'
    'Remove-LeftoverAzureResourceGroups'
    'Set-FileContent'
    'Test-SubmoduleConsistency'
) | Sort-Object

$Problems = New-Object System.Collections.Generic.List[string]

# --- every part parses ---------------------------------------------------
$PartFiles = @(Get-ChildItem -Path $PartsRoot -Filter '*.ps1' | Sort-Object Name)
if ($PartFiles.Count -eq 0) {
    $Problems.Add("No parts found under $PartsRoot.")
}

foreach ($PartFile in $PartFiles) {
    $ParseErrors = $null
    $Tokens = $null
    [System.Management.Automation.Language.Parser]::ParseFile($PartFile.FullName, [ref]$Tokens, [ref]$ParseErrors) | Out-Null
    foreach ($ParseError in $ParseErrors) {
        $Problems.Add("$($PartFile.Name): line $($ParseError.Extent.StartLineNumber): $($ParseError.Message)")
    }
}

# --- the dot-source order covers exactly the parts present ----------------
$LoaderAst = [System.Management.Automation.Language.Parser]::ParseFile($LoaderPath, [ref]$null, [ref]$null)
$PartsAssignment = $LoaderAst.Find({
        param($Node)
        $Node -is [System.Management.Automation.Language.AssignmentStatementAst] -and
        $Node.Left.Extent.Text -eq '$ModuleParts'
    }, $true)

if (-not $PartsAssignment) {
    $Problems.Add('Import-Parts.ps1 no longer assigns $ModuleParts; the load order cannot be checked.')
} else {
    # @( ... ) with one entry per line is an ArrayExpressionAst holding a statement
    # per element, not an ArrayLiteralAst, so collect the string constants instead.
    $Listed = @($PartsAssignment.Right.FindAll({
                param($Node) $Node -is [System.Management.Automation.Language.StringConstantExpressionAst]
            }, $true) | ForEach-Object { $_.Value } | Where-Object { $_ -like '*.ps1' })

    foreach ($Missing in @($PartFiles.Name | Where-Object { $Listed -notcontains $_ })) {
        $Problems.Add("parts/$Missing exists but is not listed in `$ModuleParts, so it is never loaded.")
    }
    foreach ($Extra in @($Listed | Where-Object { $PartFiles.Name -notcontains $_ })) {
        $Problems.Add("`$ModuleParts lists '$Extra', which does not exist under parts/.")
    }
}

# --- the module imports and exports its contract --------------------------
function Get-ExportedNames {
    param([string]$Path)

    $Module = Import-Module $Path -Force -PassThru
    try {
        return @($Module.ExportedFunctions.Keys | Sort-Object)
    } finally {
        Remove-Module -ModuleInfo $Module -Force
    }
}

$ManifestExports = Get-ExportedNames -Path $ManifestPath
foreach ($Name in @($ExpectedExports | Where-Object { $ManifestExports -notcontains $_ })) {
    $Problems.Add("The module no longer exports '$Name'.")
}
foreach ($Name in @($ManifestExports | Where-Object { $ExpectedExports -notcontains $_ })) {
    $Problems.Add("The module exports '$Name', which is not in the expected contract; add it to tests/Validate-Module.ps1 deliberately.")
}

# --- the manifest agrees with the module ----------------------------------
$Manifest = Import-PowerShellDataFile -Path $ManifestPath
$Declared = @($Manifest.FunctionsToExport | Sort-Object)
foreach ($Name in @($Declared | Where-Object { $ManifestExports -notcontains $_ })) {
    $Problems.Add("FunctionsToExport names '$Name', which the module does not export.")
}
foreach ($Name in @($ManifestExports | Where-Object { $Declared -notcontains $_ })) {
    $Problems.Add("The module exports '$Name', which FunctionsToExport does not name.")
}

# --- the deprecated path still works from a checkout ----------------------
$ShimExports = Get-ExportedNames -Path $ShimPath
foreach ($Name in @($ExpectedExports | Where-Object { $ShimExports -notcontains $_ })) {
    $Problems.Add("The scripts/Azure.Iot.Sdk.Test.psm1 shim no longer yields '$Name'.")
}
foreach ($Name in @($ShimExports | Where-Object { $ExpectedExports -notcontains $_ })) {
    $Problems.Add("The scripts/Azure.Iot.Sdk.Test.psm1 shim yields '$Name', which is not in the expected contract; the shim and the module must expose the same command set.")
}

if ($Problems.Count -gt 0) {
    foreach ($Problem in $Problems) { Write-Error -Message $Problem -ErrorAction Continue }
    exit 1
}

Write-Host "OK: $($PartFiles.Count) parts, $($ManifestExports.Count) exported commands, shim intact."
