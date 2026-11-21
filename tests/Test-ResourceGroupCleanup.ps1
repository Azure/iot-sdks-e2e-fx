<#
.SYNOPSIS
Drives Remove-LeftoverAzureResourceGroups with `az` stubbed, and checks which resource groups it
deletes, stamps and keeps, permanent ones included; and that updating an existing permanent group
keeps its tag.

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

# Updating an existing permanent group without -Permanent must keep the tag: the update replaces every tag.
$global:ExistingGroupTags = @{ AzIotSdkTestPermanent = 'true'; CreatedOn = $Old }
$global:PatchedTags = $null
function global:az {
    $Joined = @($args | %{ "$_" }) -join ' '
    $global:LASTEXITCODE = 0
    switch -Regex ($Joined) {
        '^account show' { return '{"id":"00000000-0000-0000-0000-000000000000","user":{"name":"stub@contoso.com"}}' }
        '^extension list' { return '[{"name":"azure-iot","version":"0.30.0"}]' }
        '^group exists' { return 'true' }
        '^group show' { return (ConvertTo-Json -Depth 3 -InputObject @{ id = '/rg/pinned'; tags = $global:ExistingGroupTags }) }
        '^rest --method PATCH' {
            $Body = $args[[array]::IndexOf($args, '--body') + 1].Substring(1)
            $global:PatchedTags = (Get-Content -Raw -Path $Body | ConvertFrom-Json).tags
            return '{}'
        }
    }
    return ''
}
$Module = Get-Module AzIotSdkTest
foreach ($Case in @(
    @{ Name = 'existing permanent'; Tags = @{ AzIotSdkTestPermanent = 'true' }; Expected = 'true' },
    @{ Name = 'existing not permanent'; Tags = @{ CreatedOn = $Old }; Expected = $null }
)) {
    $global:ExistingGroupTags = $Case.Tags
    $global:PatchedTags = $null
    & $Module { Initialize-AzIotTestResourceGroup -AzureLocation eastus2euap -ResourceGroup pinned } | Out-Null
    Assert ($null -ne $global:PatchedTags -and $global:PatchedTags.AzIotSdkTestPermanent -eq $Case.Expected) "$($Case.Name): a rerun without -Permanent patched AzIotSdkTestPermanent='$($global:PatchedTags.AzIotSdkTestPermanent)', expected '$($Case.Expected)'."
}

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: leftover resource group cleanup."
