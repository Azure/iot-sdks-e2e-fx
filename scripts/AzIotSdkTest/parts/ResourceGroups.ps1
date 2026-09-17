
# <[Azure DPS Helper Functions]>
function Get-AzureResourceGroupNamePrefix {
    <#
    .SYNOPSIS
    Returns the resource group name prefix used by this repository's pipelines.

    .DESCRIPTION
    Every resource group created by this framework is named "<prefix><guid>". The prefix is
    intentionally unique to this repository so that the scheduled cleanup pipeline in
    vsts/cleanup-leftover-resources.yaml can safely identify and delete ONLY the resource groups
    created by these pipelines. This is the single source of truth for the prefix; both
    resource-group creation and the cleanup rely on it, so do not fork this value.
    #>
    return "rg-iot-sdk-e2e-"
}

function New-AzureResourceGroupName {
    param([string]$Prefix = $(Get-AzureResourceGroupNamePrefix), [string]$OutFile = $null)

    # Azure resource group names may be at most 90 characters long.
    $MaxResourceGroupNameLength = 90

    $ResourceGroupName = $Prefix + $(New-GuidString -NoDashes)

    if ($ResourceGroupName.Length -gt $MaxResourceGroupNameLength) {
        $ResourceGroupName = $ResourceGroupName.Substring(0, $MaxResourceGroupNameLength)
    }

    if (-not [string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFileDir = Split-Path -Path $OutFile -Parent
        if ($OutFileDir -ne "" -and $(Test-Path $OutFileDir) -eq $false) {
            New-Item -ItemType Directory -Force -Path $OutFileDir | Out-Null
        }

        Set-FileContent -Path $OutFile -Content $ResourceGroupName

    }

    return $ResourceGroupName
}

# Tag this cleanup writes on a prefixed resource group that has no usable 'CreatedOn'.
# It records the first time the cleanup saw the group, which is what lets an untagged group
# age out and eventually be deleted instead of being skipped on every run forever.
$script:FirstObservedTagName = "CleanupFirstObservedOn"

function ConvertTo-UtcDateTime {
    <#
    .SYNOPSIS
    Normalizes an ISO-8601 tag value to a UTC [datetime], or $null when it cannot be parsed.

    .DESCRIPTION
    ConvertFrom-Json may hand back an ISO-8601 tag value already converted to [datetime] or
    [datetimeoffset] rather than as a string, so every shape is normalized to one UTC instant.
    Returns $null for a missing, empty or unparseable value so callers can decide what an
    unknown timestamp means rather than having an exception thrown at them.
    #>
    param($Value)

    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) {
        return $null
    }

    try {
        if ($Value -is [datetimeoffset]) {
            return $Value.UtcDateTime
        }

        if ($Value -is [datetime]) {
            return ([datetimeoffset]$Value).UtcDateTime
        }

        return [datetimeoffset]::Parse(
            [string]$Value,
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::AssumeUniversal).UtcDateTime
    } catch {
        return $null
    }
}

function Remove-LeftoverAzureResourceGroups {
    <#
    .SYNOPSIS
    Deletes resource groups created by this repository's pipelines that are older than a threshold.

    .DESCRIPTION
    Finds every resource group whose name starts with -Prefix (which defaults to the value returned
    by Get-AzureResourceGroupNamePrefix, i.e. only the resource groups created by this framework's
    pipelines) and deletes those whose 'CreatedOn' tag shows they were created more than
    -MinimumAgeHours hours ago. Resource groups created within the last -MinimumAgeHours hours are
    left untouched so that in-progress pipeline runs are never disturbed.

    A resource group whose 'CreatedOn' tag is missing or unparseable has no knowable age. Such a
    group used to be skipped on every run, which meant nothing ever deleted it and it leaked
    forever. It is now aged from the first time this cleanup observed it: the run stamps it with a
    'CleanupFirstObservedOn' tag, and a later run deletes it once that stamp is older than
    -UntaggedMinimumAgeHours. A group belonging to a run that is still in flight is therefore never
    deleted on sight; it gets a full grace period first.

    Deletions are issued with '--no-wait'; this function returns after queuing them.

    .PARAMETER Prefix
    Resource group name prefix to match. Defaults to Get-AzureResourceGroupNamePrefix (this
    repository's prefix). Another repository that reuses this function should pass the prefix its
    own pipelines use, so that only its resource groups are considered for deletion.

    .PARAMETER MinimumAgeHours
    Minimum age, in hours, a resource group must have before it is eligible for deletion. Resource
    groups created this many hours ago or less are kept. Default is 3.

    .PARAMETER UntaggedMinimumAgeHours
    How long, in hours, a resource group with no usable 'CreatedOn' tag is left alone after this
    cleanup first observes it. Deliberately longer than -MinimumAgeHours, because the age of such a
    group is unknown and the grace period is the only thing protecting an in-flight run. Default
    is 24.

    .EXAMPLE
    PS> Remove-LeftoverAzureResourceGroups -MinimumAgeHours 3

    Deletes matching resource groups older than 3 hours.

    .EXAMPLE
    PS> Remove-LeftoverAzureResourceGroups -WhatIf

    Lists the resource groups that would be deleted without deleting them, and without stamping
    any untagged group.
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Prefix = $(Get-AzureResourceGroupNamePrefix),
        [int]$MinimumAgeHours = 3,
        [int]$UntaggedMinimumAgeHours = 24
    )

    $Now = (Get-Date).ToUniversalTime()
    $Cutoff = $Now.AddHours(-$MinimumAgeHours)
    $UntaggedCutoff = $Now.AddHours(-$UntaggedMinimumAgeHours)

    Write-Host "Cleanup run (UTC)     : $($Now.ToString('o'))"
    Write-Host "Resource group prefix : '$Prefix'"
    Write-Host "Minimum age to delete : $MinimumAgeHours hour(s) (delete when created at or before $($Cutoff.ToString('o')))"
    Write-Host "Untagged grace period : $UntaggedMinimumAgeHours hour(s) after this cleanup first observes the group"

    $RawJson = az group list --query "[].{name:name, id:id, createdOn:tags.CreatedOn, firstObservedOn:tags.$($script:FirstObservedTagName), runUrl:tags.AzDevOpsRunUrl}" -o json --only-show-errors
    Stop-OnError -Step "List Azure resource groups" -Throw

    $Groups = @($RawJson | ConvertFrom-Json | Where-Object {
        $_.name -and $_.name.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)
    })

    Write-Host "Found $($Groups.Count) resource group(s) matching prefix '$Prefix'."

    $Deleted = [System.Collections.Generic.List[string]]::new()
    $Skipped = [System.Collections.Generic.List[string]]::new()
    $Stamped = [System.Collections.Generic.List[string]]::new()
    $Failed  = [System.Collections.Generic.List[string]]::new()

    foreach ($Group in $Groups) {
        $Name = $Group.name
        $CreatedOnValue = $Group.createdOn

        $CreatedOn = ConvertTo-UtcDateTime -Value $CreatedOnValue

        if ($null -eq $CreatedOn) {
            # No usable 'CreatedOn'. Such a group used to be skipped on every run forever, so
            # nothing ever deleted it. Instead, age it from the first time this cleanup saw it:
            # stamp it now, and delete it once that stamp is $UntaggedMinimumAgeHours old. A
            # group belonging to a run in flight is therefore never deleted on sight -- it gets
            # a full grace period first.
            if ([string]::IsNullOrWhiteSpace([string]$CreatedOnValue)) {
                $Reason = "no 'CreatedOn' tag"
            } else {
                $Reason = "unparseable 'CreatedOn' tag value '$CreatedOnValue'"
            }

            $FirstObserved = ConvertTo-UtcDateTime -Value $Group.firstObservedOn

            if ($null -eq $FirstObserved) {
                if ($PSCmdlet.ShouldProcess($Name, "Stamp '$($script:FirstObservedTagName)' ($Reason)")) {
                    Write-Host "STAMP  $Name : $Reason; recording first-observed time, eligible for deletion after $UntaggedMinimumAgeHours h."
                    Merge-ResourceGroupTags -ResourceGroupId $Group.id -Tags @{ $script:FirstObservedTagName = $Now.ToString('o') }
                    if ($LASTEXITCODE -ne 0) {
                        Write-Warning "Failed to stamp $Name (az exit code $LASTEXITCODE); it will be retried on the next run."
                        $global:LASTEXITCODE = 0
                        $Skipped.Add($Name)
                    } else {
                        $Stamped.Add($Name)
                    }
                } else {
                    $Skipped.Add($Name)
                }
                continue
            }

            $ObservedAgeHours = [math]::Round(($Now - $FirstObserved).TotalHours, 2)

            if ($FirstObserved -ge $UntaggedCutoff) {
                Write-Host "SKIP   $Name : $Reason; first observed $ObservedAgeHours h ago, within the $UntaggedMinimumAgeHours h untagged grace period."
                $Skipped.Add($Name)
                continue
            }

            $RunUrl = if ([string]::IsNullOrWhiteSpace($Group.runUrl)) { "(unknown run)" } else { $Group.runUrl }

            if (-not $PSCmdlet.ShouldProcess($Name, "Delete resource group (untagged; first observed $ObservedAgeHours h ago; $RunUrl)")) {
                $Skipped.Add($Name)
                continue
            }

            Write-Host "DELETE $Name : $Reason; first observed $ObservedAgeHours h ago, exceeding the $UntaggedMinimumAgeHours h untagged grace period ($RunUrl)."
            az group delete --name $Name --yes --no-wait --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Failed to queue deletion of $Name (az exit code $LASTEXITCODE)."
                $Failed.Add($Name)
            } else {
                $Deleted.Add($Name)
            }

            continue
        }

        $CreatedOnDisplay = $CreatedOn.ToString('o')
        $AgeHours = [math]::Round(($Now - $CreatedOn).TotalHours, 2)

        if ($CreatedOn -ge $Cutoff) {
            Write-Host "SKIP   $Name : age $AgeHours h is within the $MinimumAgeHours h threshold (created $CreatedOnDisplay)."
            $Skipped.Add($Name)
            continue
        }

        $RunUrl = if ([string]::IsNullOrWhiteSpace($Group.runUrl)) { "(unknown run)" } else { $Group.runUrl }

        if (-not $PSCmdlet.ShouldProcess($Name, "Delete resource group (age $AgeHours h; $RunUrl)")) {
            $Skipped.Add($Name)
            continue
        }

        Write-Host "DELETE $Name : age $AgeHours h exceeds $MinimumAgeHours h (created $CreatedOnDisplay; $RunUrl)."
        az group delete --name $Name --yes --no-wait --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to queue deletion of $Name (az exit code $LASTEXITCODE)."
            $Failed.Add($Name)
        } else {
            $Deleted.Add($Name)
        }
    }

    Write-Host ""
    Write-Host "==== Cleanup summary ===="
    Write-Host "Queued for deletion        : $($Deleted.Count)"
    Write-Host "Skipped / not processed    : $($Skipped.Count)"
    Write-Host "Stamped (untagged, ageing) : $($Stamped.Count)"
    Write-Host "Failed to queue            : $($Failed.Count)"
    if ($Deleted.Count -gt 0) { Write-Host "Deleted: $($Deleted -join ', ')" }
    if ($Stamped.Count -gt 0) { Write-Host "Stamped: $($Stamped -join ', ')" }
    if ($Failed.Count -gt 0)  { Write-Host "Failed : $($Failed -join ', ')" }

    if ($Failed.Count -gt 0) {
        throw "$($Failed.Count) resource group deletion(s) could not be queued."
    }
}


# <[Azure DevOps]>

function Get-AzureDevOpsRunUrl {
    if ($env:SYSTEM_COLLECTIONURI -and $env:SYSTEM_TEAMPROJECT -and $env:BUILD_BUILDID) {
        return "$($env:SYSTEM_COLLECTIONURI)$($env:SYSTEM_TEAMPROJECT)/_build/results?buildId=$($env:BUILD_BUILDID)"
    } else {
        return $null
    }
}
