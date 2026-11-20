<#
.SYNOPSIS
Drives Remove-LeftoverAzureResourceGroups with `az` stubbed, and checks which resource groups it
deletes, stamps and keeps, permanent ones included.

.DESCRIPTION
Deletes nothing and needs no credentials. `az` is replaced by a stub that lists fixed resource
groups and records every call.

.EXAMPLE
pwsh -NoProfile -File tests/Test-ResourceGroupCleanup.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $RepoRoot 'scripts/AzIotSdkTest/AzIotSdkTest.psd1') -Force

$Old = (Get-Date).ToUniversalTime().AddDays(-2).ToString('o')
$Recent = (Get-Date).ToUniversalTime().ToString('o')
$Groups = @(
    @{ name = 'ci-old'; id = '/rg/ci-old'; createdOn = $Old },
    @{ name = 'ci-recent'; id = '/rg/ci-recent'; createdOn = $Recent },
    @{ name = 'ci-untagged'; id = '/rg/ci-untagged' },
    @{ name = 'ci-permanent'; id = '/rg/ci-permanent'; createdOn = $Old; permanent = 'true' },
    @{ name = 'ci-permanent-untagged'; id = '/rg/ci-permanent-untagged'; permanent = 'True' },
    @{ name = 'ci-not-permanent'; id = '/rg/ci-not-permanent'; createdOn = $Old; permanent = 'false' },
    @{ name = 'other-old'; id = '/rg/other-old'; createdOn = $Old }
)

$global:Calls = New-Object System.Collections.Generic.List[string]
function global:az {
    $Joined = @($args | %{ "$_" }) -join ' '
    $global:Calls.Add($Joined)
    $global:LASTEXITCODE = 0
    if ($Joined -match '^group list') { return (ConvertTo-Json -Depth 3 -InputObject $Groups) }
    return ''
}

$Problems = New-Object System.Collections.Generic.List[string]
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { $Problems.Add($Message) } }

Remove-LeftoverAzureResourceGroups -Prefix 'ci-' | Out-Null

$Deleted = @($Calls | ?{ $_ -match '^group delete --name (\S+)' } | %{ ($_ -split ' ')[3] } | Sort-Object)
$Stamped = @($Calls | ?{ $_ -match '^rest --method PATCH --url \S+/rg/(\S+)/providers/Microsoft.Resources/tags' } | %{ $Matches[1] })
Assert (($Deleted -join ',') -eq 'ci-not-permanent,ci-old') "deleted '$($Deleted -join ',')', expected 'ci-not-permanent,ci-old'."
Assert (($Stamped -join ',') -eq 'ci-untagged') "stamped '$($Stamped -join ',')', expected 'ci-untagged': a permanent group must not be stamped."
Assert ((@($Calls | ?{ $_ -match '^group list' }) -join '') -match 'permanent:tags\.AzIotSdkTestPermanent') "the group list must read the AzIotSdkTestPermanent tag."

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: leftover resource group cleanup."
