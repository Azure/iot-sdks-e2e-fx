
function Install-AzureIotCliExtension {
    $Extension = $(az extension list --output json --only-show-errors | ConvertFrom-Json | ?{$_.name -eq "azure-iot"})

    if ($null -ne $Extension -and $Extension.version -ne $script:AzureIotCliExtensionVersion) {
        Write-Host "Azure IoT extension $($Extension.version) found; removing (pinned to $($script:AzureIotCliExtensionVersion))."
        az extension remove --name azure-iot --only-show-errors | Out-Null
        Stop-OnError -Step "Remove Azure IoT extension"
        $Extension = $null
    }

    if ($null -eq $Extension) {
        Write-Host "Installing Azure IoT extension $($script:AzureIotCliExtensionVersion)."
        az extension add --source $script:AzureIotCliExtensionSource --yes --only-show-errors | Out-Null
        Stop-OnError -Step "Install Azure IoT extension"
    }

    # What actually ended up installed. When a provisioning command goes missing
    # ("'adr' is misspelled or not recognized"), this is the first thing worth
    # seeing in the log.
    #
    # Capture the table and re-emit it with Write-Host rather than letting the
    # native command write straight to the pipeline. A bare `az` call puts its
    # stdout on the SUCCESS stream, which flows out of this function and into
    # the caller's return value -- New-AzIotTestEnvironment then returns
    # Object[] (table lines + the TestEnvironmentInfo) instead of a single
    # object, and any caller with a typed [TestEnvironmentInfo] parameter fails
    # with "Cannot convert the System.Object[] value ... to TestEnvironmentInfo".
    # Write-Host is also the only form that reliably reaches the log from inside
    # the AzureCLI@2 task, which swallows bare native stdout.
    Write-Host "Azure CLI IoT extension version details:"
    Write-Host (az extension list --output table --only-show-errors | Out-String)
}

function Invoke-WithRetry {
    <#
    .SYNOPSIS
    Runs a script block, retrying with backoff while its stderr matches a
    pattern known to be transient.

    .DESCRIPTION
    Takes the command as a script block so call sites keep ordinary `az` syntax
    -- named arguments, line continuations, and `| ConvertFrom-Json` all stay
    exactly where they were. Whatever the block returns is returned unchanged.

    The motivating case is Azure RBAC propagation. `az role assignment create`
    returns as soon as the assignment reaches the RBAC store, but the resource
    providers that ENFORCE it cache permissions and can take minutes to observe
    the change. Handing a freshly-granted identity to another provider therefore
    fails with an access-denied error that would have succeeded moments later.

    -RetryOnPattern keeps that narrow: retrying every failure would turn genuine
    errors (bad name, quota exhausted, invalid SKU) into slow failures instead
    of fast ones.

    stderr is redirected to a temp file rather than merged with `2>&1`, for two
    reasons: merged native stderr raises NativeCommandError under
    `$ErrorActionPreference = 'Stop'` (which the azure/powershell task sets),
    and merging would concatenate CLI preview/extension notices into the JSON
    the block is piping to ConvertFrom-Json.

    .PARAMETER Step
    Human-readable step name, used in the error message.

    .PARAMETER Command
    Script block to run. Runs in its defining scope, so it can use the caller's
    variables normally.

    .PARAMETER RetryOnPattern
    Regex matched against stderr. Only matching failures are retried.

    .PARAMETER MaxAttempts
    Total attempts, including the first.

    .PARAMETER InitialDelaySeconds
    Delay before the second attempt; doubles thereafter.

    .EXAMPLE
    PS> $Hub = Invoke-WithRetry -Step "Create Azure IoT Hub" -RetryOnPattern '400913' -Command {
    PS>     az iot hub create --name "$IotHubName" --resource-group "$ResourceGroup" | ConvertFrom-Json
    PS> }
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Step,
        [Parameter(Mandatory = $true)][scriptblock]$Command,
        [Parameter(Mandatory = $true)][string]$RetryOnPattern,
        [int]$MaxAttempts = 4,
        [int]$InitialDelaySeconds = 30
    )

    $Delay = $InitialDelaySeconds

    for ($Attempt = 1; $Attempt -le $MaxAttempts; $Attempt++) {
        $StdErrFile = New-TempFile
        try {
            $Result = $null
            $Caught = $null
            $global:LASTEXITCODE = 0

            try {
                $Result = & $Command 2>$StdErrFile
            } catch {
                # e.g. ConvertFrom-Json choking on the empty stdout of a failed
                # command. The real diagnosis is the exit code plus stderr below.
                $Caught = $_
            }

            $ExitCode = $LASTEXITCODE

            $StdErr = $null
            if (Test-Path -Path $StdErrFile) {
                $StdErr = Get-Content -Path $StdErrFile -Raw
            }

            if (-not [string]::IsNullOrWhiteSpace($StdErr)) {
                # Printed on success too: az writes preview/extension notices to
                # stderr, and those are worth having in the log.
                Write-Host "Output for `"$Step`" (attempt $Attempt of $MaxAttempts):"
                Write-Host $StdErr.Trim()
            }

            if ($ExitCode -eq 0 -and $null -eq $Caught) {
                return $Result
            }

            $IsLastAttempt = ($Attempt -ge $MaxAttempts)
            $IsRetryable = ($null -ne $StdErr) -and ($StdErr -match $RetryOnPattern)

            if ($IsLastAttempt -or -not $IsRetryable) {
                if ($null -ne $Caught) {
                    Write-Host $Caught.ToString()
                }
                # Hand the command's own exit code to Stop-OnError so the failure
                # is reported exactly like a non-retrying call site.
                $global:LASTEXITCODE = if ($ExitCode -ne 0) { $ExitCode } else { 1 }
                Stop-OnError -Step $Step
                return $null
            }

            Write-Host "`"$Step`" hit a transient error; retrying in $Delay seconds."
            Start-Sleep -Seconds $Delay
            $Delay = $Delay * 2
        }
        finally {
            Remove-Item -Path $StdErrFile -ErrorAction SilentlyContinue
        }
    }
}

function Wait-AzRoleAssignment {
    <#
    .SYNOPSIS
    Blocks until the given role assignments can be read back at their scope.

    .DESCRIPTION
    `az role assignment create` exiting 0 only means the assignment reached the
    RBAC store. Reading it back confirms that much, which is the earliest point
    at which propagation to enforcing resource providers can even begin.

    This is NOT sufficient on its own -- providers cache permissions
    independently -- so callers must still tolerate an access-denied answer
    afterwards (see Invoke-WithRetry). Doing both keeps the common case
    fast while still converging in the slow case.

    Never fails provisioning: on timeout it warns and returns, because the
    operation that actually matters is retried by its caller.

    .PARAMETER PrincipalId
    Object id of the principal the roles were granted to.

    .PARAMETER Scope
    Resource id the assignments were created against.

    .PARAMETER RoleDefinitionIds
    Role definition GUIDs expected to be present.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$PrincipalId,
        [Parameter(Mandatory = $true)][string]$Scope,
        [Parameter(Mandatory = $true)][string[]]$RoleDefinitionIds,
        [int]$TimeoutSeconds = 120,
        [int]$PollIntervalSeconds = 10
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $LastQueryError = $null

    while ($true) {
        # The query itself must never abort provisioning. `az` can fail (throttling,
        # transient ARM error) and ConvertFrom-Json then throws on empty/non-JSON
        # stdout -- which under $ErrorActionPreference = 'Stop' would propagate and
        # kill the run. Treat any failure here as "not visible yet" and keep polling.
        $Assignments = $null
        $LastQueryError = $null
        try {
            $global:LASTEXITCODE = 0
            $Assignments = az role assignment list --assignee "$PrincipalId" --scope "$Scope" --only-show-errors | ConvertFrom-Json
            if ($LASTEXITCODE -ne 0) {
                # az failed but wrote nothing to stdout, so ConvertFrom-Json had
                # nothing to choke on and did not throw. Record it explicitly.
                $LastQueryError = "az exited with code $LASTEXITCODE"
            }
        } catch {
            $LastQueryError = $_.Exception.Message
        }

        $Observed = @()
        if ($null -ne $Assignments) {
            $Observed = @($Assignments | ForEach-Object { $_.roleDefinitionId })
        }

        $Missing = @($RoleDefinitionIds | Where-Object {
            $RoleId = $_
            -not ($Observed | Where-Object { $_ -like "*$RoleId" })
        })

        if ($Missing.Count -eq 0) {
            Write-Host "All $($RoleDefinitionIds.Count) role assignment(s) are visible at $Scope."
            return
        }

        if ((Get-Date) -ge $Deadline) {
            Write-Host "WARNING: $($Missing.Count) role assignment(s) still not visible after $TimeoutSeconds seconds: $($Missing -join ', '). Continuing; the dependent step retries on access-denied."
            if ($null -ne $LastQueryError) {
                # Surface it: repeated query failures mean the wait told us nothing,
                # which is worth knowing when diagnosing a later access-denied error.
                Write-Host "WARNING: the last role assignment query also failed: $LastQueryError"
            }
            return
        }

        Write-Host "Waiting for $($Missing.Count) role assignment(s) to become visible; polling again in $PollIntervalSeconds seconds."
        Start-Sleep -Seconds $PollIntervalSeconds
    }
}

function Merge-ResourceGroupTags {
    <#
    .SYNOPSIS
    Adds tags to a resource group without disturbing the tags it already carries.

    .DESCRIPTION
    Set-ResourceGroupTags PATCHes the resource group itself, which replaces the whole tags
    collection with whatever is supplied. That is correct where the caller knows the complete
    desired set, but wrong for adding a single tag to a group whose other tags -- for example
    'AzDevOpsRunUrl' -- must survive. This uses the dedicated tags endpoint with an explicit
    Merge operation instead, so existing tags are left alone.
    #>
    param(
        [string]$ResourceGroupId,
        [Hashtable]$Tags
    )

    $BodyFile = New-TempFile
    try {
        $Payload = @{ operation = "Merge"; properties = @{ tags = $Tags } } | ConvertTo-Json -Compress -Depth 5
        Set-FileContent -Path $BodyFile -Content $Payload
        az rest `
            --method PATCH `
            --url "https://management.azure.com${ResourceGroupId}/providers/Microsoft.Resources/tags/default?api-version=2021-04-01" `
            --body "@$BodyFile" `
            --only-show-errors | Out-Null
    }
    finally {
        Remove-Item -Path $BodyFile -ErrorAction SilentlyContinue
    }
}

function Set-ResourceGroupTags {
    param(
        [string]$ResourceGroupId,
        [Hashtable]$Tags
    )

    $bodyFile = New-TempFile
    try {
        $payload = @{ tags = $Tags } | ConvertTo-Json -Compress
        Set-FileContent -Path $bodyFile -Content $payload
        az rest --method PATCH --url "https://management.azure.com${ResourceGroupId}?api-version=2024-03-01" --body "@$bodyFile" --only-show-errors | Out-Null
    }
    finally {
        Remove-Item -Path $bodyFile -ErrorAction SilentlyContinue
    }
}

function New-AzureResourceGroup {
    <#
    .SYNOPSIS
    Creates an Azure resource group that already carries its tags the moment it exists.

    .DESCRIPTION
    Creating the group and tagging it must be a single operation. When they are two
    operations ('az group create' followed by a tag update), a run that dies in between --
    an agent that is cancelled, times out, or loses its network -- leaves an untagged
    resource group behind. Remove-LeftoverAzureResourceGroups cannot determine the age of an
    untagged group, so it skips it on every run and the group survives forever.

    The tags are sent as JSON in a request body file rather than as '--tags key=value'
    arguments, for the same reason Set-ResourceGroupTags does it: under the AzureCLI@2 task
    the array-argument form collapses every pair into a single tag value.

    .PARAMETER SubscriptionId
    Subscription the resource group is created in.

    .PARAMETER ResourceGroup
    Name of the resource group to create.

    .PARAMETER Location
    Azure location for the resource group.

    .PARAMETER Tags
    Tags to apply as part of the creation itself.
    #>
    param(
        [string]$SubscriptionId,
        [string]$ResourceGroup,
        [string]$Location,
        [Hashtable]$Tags
    )

    if ($null -eq $Tags) {
        $Tags = @{}
    }

    $BodyFile = New-TempFile
    try {
        $Payload = @{ location = $Location; tags = $Tags } | ConvertTo-Json -Compress
        Set-FileContent -Path $BodyFile -Content $Payload

        return az rest `
            --method PUT `
            --url "https://management.azure.com/subscriptions/$SubscriptionId/resourcegroups/$($ResourceGroup)?api-version=2024-03-01" `
            --body "@$BodyFile" `
            --only-show-errors | ConvertFrom-Json
    }
    finally {
        Remove-Item -Path $BodyFile -ErrorAction SilentlyContinue
    }
}
