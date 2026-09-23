

# <[Azure Device Registry (ADR) Helper Functions]>

# Tag the reference E2E harness for this feature puts on every namespace it creates and links. ADR
# reads it as a feature flag: without it the linking saga takes a different path and reports the
# resource it is linking as unreadable.
$script:AdrNamespaceTags = @{ useMiSdk = "true" }

# ADR resources are created through ARM directly: the azure-iot CLI extension only ever exposed the
# public-preview object model (a namespace credential holding policies, selected by name) and has no
# command for the certificate-authority model that replaced it.
#
# Overridable from the environment so a cloud or region where one of these versions is not registered
# can be unblocked without a code change.
# The namespace/link api-version. 2026-11-02-preview links only where the subscription is already
# enabled for it; 2026-11-01-preview links on both subscriptions this suite has been run against,
# including one where every 2026-11-02-preview attempt failed LinkableResourceNotReady. The prime
# and the link must stay on ONE version: the namespace projects a different SystemAssigned
# principalId per api-version, so granting the role at one and linking at another authorizes an
# identity the link never uses.
$script:AdrApiVersion = if ($env:ADR_API_VERSION) { $env:ADR_API_VERSION } else { "2026-11-01-preview" }
$script:DpsControlPlaneApiVersion = if ($env:DPS_CONTROL_PLANE_API_VERSION) { $env:DPS_CONTROL_PLANE_API_VERSION } else { "2026-03-01-preview" }
$script:DpsEnrollmentApiVersion = if ($env:DPS_ENROLLMENT_API_VERSION) { $env:DPS_ENROLLMENT_API_VERSION } else { "2026-11-01" }
$script:IotHubApiVersion = if ($env:IOT_HUB_API_VERSION) { $env:IOT_HUB_API_VERSION } else { "2026-06-01-preview" }

# Azure Device Registry Contributor: namespaces/read, namespaces/devices/*, and the data actions,
# including the certificate issuance a CSR needs.
$script:AdrContributorRoleId = "a5c3590a-3a1a-4cd4-9648-ea0a32b15137"
# IoT Hub Data Contributor: device registration and enrollment writes run as a managed identity.
$script:IotHubDataContributorRoleId = "4fc6c259-987e-4a07-842e-c321cc9d413f"
# Contributor.
$script:ContributorRoleId = "b24988ac-6180-42a0-ab88-20f7382dd24c"

# The namespace link saga runs as the namespace's managed identity, whose grants are eventually
# consistent. Until they replicate, linking fails with one of these -- either outright, or by
# settling an endpoint to Failed after the fact. Both are recovered by re-submitting the same
# namespace, whose identity keeps replicating; everything else fails immediately.
$script:AdrRolePropagationPattern = 'AdrMiNotAuthorized|LinkableResourceNotReady|AuthorizationFailed|LinkInitiateFailed|NamespaceMiTokenAcquisitionFailed|OutboundIdentityUnavailable'

# ARM itself can answer a link submission with a transient failure -- a 503 'Our services aren't
# available right now' has ended a run mid-way through the retries. It says nothing about the link,
# so it is retried rather than failing the run.
# Matched on the words ARM uses, not on bare status numbers: a correlation id or a resource name
# can contain '503' and a false match would keep retrying a real error.
$script:ArmTransientPattern = 'Service ?Unavailable|Gateway ?Timeout|Too ?Many ?Requests|InternalServerError|ServerTimeout|ServerBusy'
$script:AdrLinkMaxAttempts = 12
# Whole-namespace recovery cycles: recreate and re-grant if the in-place link retries are exhausted.
$script:AdrLinkMaxCycles = 2

function Get-DpsArmHost {
    <#
    .SYNOPSIS
    Returns the ARM host DPS control-plane calls go to for a location.

    .DESCRIPTION
    The DPS manifest that carries the ADR linking surface is registered regionally in the canary
    locations, so a DPS created through the global host there does not come up with it. Everything
    else, including the namespace and the hub, uses the global host.
    #>
    param([string]$Location)

    if ($Location -like "*euap") {
        return "https://$Location.management.azure.com"
    }
    return "https://management.azure.com"
}

function Remove-AdrNamespace {
    <#
    .SYNOPSIS
    Deletes an ADR namespace and waits for it to be gone.

    .DESCRIPTION
    Recovery of last resort for a namespace whose identity never becomes usable to the linking saga.
    Recreating it mints a fresh identity; the grants are then made against that one.
    #>
    param(
        [string]$NamespaceId,
        [int]$TimeoutSeconds = 600
    )

    $Url = "https://management.azure.com$($NamespaceId)?api-version=$($script:AdrApiVersion)"
    # Retried: a discarded transient failure would leave the loop below polling a namespace that
    # was never asked to go, turning a brief outage into the full timeout.
    Write-Host "Deleting ADR namespace to recover the link."
    try {
        Invoke-WithRetry -Step "Delete ADR namespace" -ThrowOnFailure `
            -RetryOnPattern $script:ArmTransientPattern -MaxAttempts 3 -InitialDelaySeconds 10 -Command {
            # NOT -AllowFailure: that resets the exit code, so the retry would see success and the
            # retry this exists for would never happen.
            Invoke-AzRest -Method DELETE -Url $Url
        } | Out-Null
    }
    catch {
        # Already gone is the end state being asked for, not a failure. Anything else propagates.
        if ("$_" -notmatch 'ResourceNotFound|NotFound|\(404\)|was not found') { throw }
        Write-Host "ADR namespace was already absent."
        return
    }

    # Waits for the namespace to be GONE, not merely unreadable: a transient failure also returns
    # nothing, and reading that as "deleted" lets the next create race a namespace that still
    # exists. Only a not-found ends the wait. stderr goes to a file rather than being merged with
    # 2>&1, for the reason Invoke-WithRetry gives: merged native stderr raises NativeCommandError
    # under the Stop preference the pipeline task sets, so an ordinary 404 would throw here first.
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ($true) {
        $StdErrFile = New-TempFile
        try {
            $null = az rest --method GET --url $Url --resource "https://management.azure.com/" --only-show-errors 2>$StdErrFile
            $Found = ($LASTEXITCODE -eq 0)
            $global:LASTEXITCODE = 0
            $StdErr = if (Test-Path -Path $StdErrFile) { Get-Content -Path $StdErrFile -Raw } else { "" }
        }
        finally {
            Remove-Item -Path $StdErrFile -ErrorAction SilentlyContinue
        }

        if (-not $Found -and $StdErr -match 'ResourceNotFound|NotFound|\(404\)|was not found') {
            return
        }
        if ((Get-Date) -ge $Deadline) {
            throw "ADR namespace was not confirmed deleted within $TimeoutSeconds seconds."
        }
        Start-Sleep -Seconds 10
    }
}

function New-AdrNamespace {
    <#
    .SYNOPSIS
    Creates a system-assigned-identity ADR namespace and returns it.

    .DESCRIPTION
    Certificate management is no longer switched on at namespace creation, and no policy name is
    supplied here: both are properties of the certificate authorities created under the namespace
    afterwards (see New-AdrCertificateAuthority).
    #>
    param(
        [string]$SubscriptionId,
        [string]$ResourceGroup,
        [string]$NamespaceName,
        [string]$Location
    )

    $Url = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.DeviceRegistry/namespaces/$($NamespaceName)?api-version=$($script:AdrApiVersion)"

    Write-Host "Creating ADR namespace ($NamespaceName)"
    Invoke-AzRest -Method PUT -Url $Url -Body @{
        location = $Location
        identity = @{ type = "SystemAssigned" }
        tags = $script:AdrNamespaceTags
    } | Out-Null

    Wait-AzProvisioningState -Url $Url -Step "ADR namespace ($NamespaceName)"

    # Re-read rather than use the PUT response: the principalId is assigned asynchronously and can
    # still be absent from the body the create returned.
    return Invoke-AzRest -Url $Url
}

function Connect-AdrNamespace {
    <#
    .SYNOPSIS
    Attaches an IoT Hub and a DPS to an ADR namespace, and waits for the link to complete.

    .DESCRIPTION
    Replaces the public-preview wiring, where the hub and DPS were pointed at the namespace with
    '--ns-resource-id'/'--ns-identity-id' as they were created. That now fails validation; the
    relationship is expressed on the NAMESPACE instead, as endpoints: the hub as a messaging
    endpoint, the DPS as a provisioning one. Both go in a single write, because ADR refuses a
    messaging endpoint unless the namespace also has a provisioning one.

    The call returns immediately with the endpoint at linkingState=InProgress; ADR completes the link
    asynchronously. The link runs as the namespace identity, so one attempted before that identity's
    grants have replicated fails on a role-propagation error -- either outright, or by settling the
    endpoint to Failed once it runs. A failed endpoint is re-PUTtable, so the link is re-submitted
    against the same namespace, whose identity keeps replicating. A failure for any other reason is
    final and is raised on the spot.

    Linking can also leave the namespace at provisioningState=Failed with the endpoint Succeeded.
    That is healed here, because otherwise device registration later fails with errorCode 403000.
    #>
    param(
        [string]$NamespaceId,
        [string]$Location,
        [string]$IotHubId,
        [string]$DpsId,
        # The principal the namespace's role grants were made against. The link resends the
        # identity, and if a write ever replaced that principal the grants would point at one that
        # no longer exists -- which ADR reports as the linked resource being unreadable, exactly
        # like a grant that has not replicated. Checked so the two can be told apart.
        [string]$ExpectedPrincipalId,
        # How long one attempt waits for the endpoints to settle. Parameterised so a test can drive
        # the timeout path without waiting out the real budget.
        [int]$LinkTimeoutSeconds = 900
    )

    $Url = "https://management.azure.com$($NamespaceId)?api-version=$($script:AdrApiVersion)"
    $LinkBody = @{
        location = $Location
        identity = @{ type = "SystemAssigned" }
        tags = $script:AdrNamespaceTags
        properties = @{
            messaging = @{ endpoints = @{ "hub-1" = @{
                endpointType = "Microsoft.Devices/IotHubs"
                resourceId = $IotHubId
                inboundCallerIdentity = @{ type = "SystemAssigned" }
                provisioning = @{ availability = "Available"; allocationWeight = 1 }
            } } }
            provisioning = @{ endpoints = @{ "dps-1" = @{
                endpointType = "Microsoft.Devices/provisioningServices"
                resourceId = $DpsId
                inboundCallerIdentity = @{ type = "SystemAssigned" }
            } } }
        }
    }

    for ($Attempt = 1; $Attempt -le $script:AdrLinkMaxAttempts; $Attempt++) {
        Write-Host "Linking IoT Hub and DPS to ADR namespace (attempt $Attempt of $($script:AdrLinkMaxAttempts))"
        # Retries a link REJECTED outright; an accepted link that later fails is handled below.
        # Throws rather than exiting: a rejected link is recoverable by the cycle around this, and
        # Stop-OnError would otherwise end the run before the catch could see it.
        Invoke-WithRetry -Step "Link IoT Hub and DPS to ADR namespace" -ThrowOnFailure `
            -RetryOnPattern "$($script:AdrRolePropagationPattern)|$($script:ArmTransientPattern)" -MaxAttempts 3 -Command {
            Invoke-AzRest -Method PUT -Url $Url -Body $LinkBody
        } | Out-Null

        # Endpoint linkingState is the source of truth: the namespace itself can read Succeeded while
        # an endpoint is still InProgress, and a failed endpoint is where the reason is recorded.
        $Deadline = (Get-Date).AddSeconds($LinkTimeoutSeconds)
        $Reads = 0
        $ReadFailures = 0
        while ($true) {
            # As in Wait-AzProvisioningState, a failed read during a poll that runs for minutes is
            # transient and says nothing about the link, so it costs an attempt rather than the run.
            $Namespace = Invoke-AzRest -Url $Url -AllowFailure
            $Reads++
            # A read that fails returns $null, and every property access below then yields nothing,
            # so a namespace that cannot be READ looks exactly like one whose link has not started.
            # Counted and reported, because the two call for opposite responses and the difference
            # is otherwise invisible for the whole of the timeout.
            if ($null -eq $Namespace) {
                $ReadFailures++
            }
            # Each group is read separately and nulls are dropped: an ABSENT group still yields one
            # entry when enumerated, so a missing DPS endpoint would otherwise be counted as though
            # it were present and reported as an unnamed endpoint with no state.
            $Messaging = @($Namespace.properties.messaging.endpoints.PSObject.Properties | ?{ $null -ne $_ })
            $Provisioning = @($Namespace.properties.provisioning.endpoints.PSObject.Properties | ?{ $null -ne $_ })
            # `updating` is read for reporting only. We never submit one, but ADR can carry an
            # endpoint there, so an endpoint that is missing from the two sections we do submit is
            # worth distinguishing from one that moved.
            $Updating = @($Namespace.properties.updating.endpoints.PSObject.Properties | ?{ $null -ne $_ })

            # A namespace whose identity no longer matches the principal its grants were made
            # against cannot work: the link may still report success, but every later ADR call runs
            # as an identity holding nothing. Raised so the cycle around this recreates and regrants
            # rather than carrying on with an environment that is already unusable.
            $Principal = $Namespace.identity.principalId
            if ($ExpectedPrincipalId -and $Principal -and $Principal -ne $ExpectedPrincipalId) {
                throw "AdrMiNotAuthorized: the namespace identity is $Principal but its role grants were made against $ExpectedPrincipalId, so those grants hold nothing."
            }
            $Endpoints = $Messaging + $Provisioning
            $States = @($Endpoints | %{ $_.Value.linkingState })
            $Failed = @($Endpoints | ?{ $_.Value.linkingState -eq "Failed" })

            # A failure ends the attempt immediately. Waiting for the other endpoints to settle would
            # only burn the deadline: one of them may never carry a state at all.
            if ($Failed.Count -gt 0) {
                break
            }

            # The link is complete only when BOTH groups carry an endpoint and every one of them
            # Succeeded. Counting endpoints alone is not enough: ADR can return the hub and omit the
            # DPS, and setup would then create the CA and the enrollments against an unlinked DPS.
            if ($Messaging.Count -gt 0 -and $Provisioning.Count -gt 0 -and
                @($States | ?{ $_ -ne "Succeeded" }).Count -eq 0) {
                break
            }

            if ((Get-Date) -ge $Deadline) {
                # A namespace that never read at all is a DIFFERENT failure from a link that
                # stalled, and the endpoint states cannot tell them apart because both render as
                # nothing. Said explicitly, because the two call for opposite responses.
                $Unreadable = if ($Reads -gt 0 -and $ReadFailures -eq $Reads) {
                    " The namespace could not be read on any of the $Reads attempts, so this is a failure to READ the namespace, not a link that stalled."
                } elseif ($ReadFailures) {
                    " $ReadFailures of $Reads namespace reads failed."
                } else {
                    ""
                }
                throw "ADR namespace link did not complete within $LinkTimeoutSeconds seconds (endpoint states: $($States -join ', ')).$Unreadable"
            }

            Write-Host "Waiting for ADR namespace link (endpoint states: $($States -join ', '))$(if ($ReadFailures) { " [$ReadFailures of $Reads namespace reads failed]" })."
            Start-Sleep -Seconds 15
        }

        if ($Failed.Count -eq 0) {
            break
        }

        # Every endpoint is reported, not just the first failure. Which endpoint failed and which
        # succeeded is the first thing asked of a link failure, and naming only one leaves it
        # ambiguous whether the others were fine or simply not mentioned.
        $Summary = (@(
            $(if ($Messaging.Count -eq 0) { "messaging=<no endpoint>" })
            $(if ($Provisioning.Count -eq 0) { "provisioning=<no endpoint>" })
            $($Endpoints | %{
                $Code = $_.Value.linkingError.code
                "$($_.Name)=$($_.Value.linkingState)$(if ($Code) { " ($Code)" })"
            })
            $($Updating | %{ "updating/$($_.Name)=$($_.Value.linkingState)" })
        ) | ?{ $_ }) -join ', '

        # A permanent failure on ANY endpoint ends it. Judging only the first would retry a
        # recoverable hub error while a permanent DPS one went unmentioned until the budget ran out.
        $Permanent = @($Failed | ?{ $_.Value.linkingError.code -notmatch $script:AdrRolePropagationPattern })
        if ($Permanent.Count -gt 0 -or $Attempt -eq $script:AdrLinkMaxAttempts) {
            $Detail = ($Failed | %{ "$($_.Name): $($_.Value.linkingError | ConvertTo-Json -Depth 5 -Compress)" }) -join "; "
            throw "ADR namespace link failed. Endpoints: $Summary. Errors: $Detail"
        }

        # Grows with each attempt, to a cap: each re-submission actively probes whether the grants
        # have taken effect, so several short waits beat one long blind sleep.
        $RetryWait = [Math]::Min(60, 30 * $Attempt)
        Write-Host "Link not complete ($Summary) while the namespace role assignments replicate; re-submitting in $RetryWait seconds."
        Start-Sleep -Seconds $RetryWait
    }

    # Heal a namespace left Failed by an otherwise successful link. A tags-only update re-runs
    # namespace reconciliation; re-sending the endpoints instead is rejected as immutable. The state
    # can read Failed for a while after the update is accepted, so it is polled rather than judged
    # on first read.
    if ($Namespace.properties.provisioningState -eq "Failed") {
        Write-Host "Namespace left at provisioningState=Failed after linking; reconciling."
        # This module always creates the namespace with tags, but a namespace it merely found could
        # have none, and piping a null property into ForEach-Object still runs the body once, with a
        # null key. Guarded so the reconcile does not fail on one.
        $Tags = @{}
        if ($null -ne $Namespace.tags) { $Namespace.tags.PSObject.Properties | %{ $Tags[$_.Name] = $_.Value } }
        # The namespace feature tag is re-asserted rather than merely carried over: it selects which
        # identity the link authorizes against, so a namespace that reached here without it would be
        # healed into a state the link still cannot use.
        $script:AdrNamespaceTags.GetEnumerator() | %{ $Tags[$_.Key] = $_.Value }
        $Tags["AdrReconcileUtc"] = (Get-Date).ToUniversalTime().ToString("o")
        Invoke-AzRest -Method PATCH -Url $Url -Body @{ tags = $Tags } | Out-Null

        # Not Wait-AzProvisioningState: it treats the first Failed read as terminal, which is the
        # state being healed. The reconcile is accepted before the namespace stops reporting it, so
        # Failed is tolerated here until it clears or the deadline passes.
        $Deadline = (Get-Date).AddSeconds(300)
        while ($true) {
            $State = (Invoke-AzRest -Url $Url -AllowFailure).properties.provisioningState
            if ($State -eq "Succeeded") {
                return
            }
            if ((Get-Date) -ge $Deadline) {
                throw "ADR namespace did not recover from provisioningState=Failed within 300 seconds (last state: '$State')."
            }
            Write-Host "Waiting for the ADR namespace reconcile (provisioningState=$State)."
            Start-Sleep -Seconds 10
        }
    }
}

function New-AdrCertificateAuthority {
    <#
    .SYNOPSIS
    Creates the ADR certificate authority chain and the certificate policy devices are issued from.
    Returns the name of the issuing CA that enrollments must reference.

    .DESCRIPTION
    Replaces the public-preview 'namespaces/<ns>/credentials/default/policies/<policy>' object, which
    no longer exists. Leaf issuance now requires a full chain, because a certificate policy has to
    hang off an ISSUING CA -- ADR rejects a policy created under a root with 409
    PolicyRequiresIssuingCa:

        namespaces/<ns>/certificateAuthorities/<ca>-root                          self-managed root
        namespaces/<ns>/certificateAuthorities/<ca>                               issuing CA (ICA)
        namespaces/<ns>/certificateAuthorities/<ca>/certificatePolicies/<policy>   leaf issuance

    The root is self-managed, so ADR generates its key and certificate on create. The ICA is issued
    internally by that root (issuerType=Microsoft). Enrollments reference the ICA, never the root.

    Must run AFTER the namespace is linked to the IoT Hub: creating the ICA makes ADR sync the CA
    certificate to the linked hub, and with no link there is no hub to sync it to. The
    'credential sync' step of the previous model is gone -- trust now flows over that link.
    #>
    param(
        [string]$NamespaceId,
        [string]$Location,
        [string]$CertificateAuthorityName,
        [string]$PolicyName,
        [int]$LeafValidityDays = 30
    )

    $RootUrl   = "https://management.azure.com$NamespaceId/certificateAuthorities/$($CertificateAuthorityName)-root?api-version=$($script:AdrApiVersion)"
    $IcaUrl    = "https://management.azure.com$NamespaceId/certificateAuthorities/$($CertificateAuthorityName)?api-version=$($script:AdrApiVersion)"
    $PolicyUrl = "https://management.azure.com$NamespaceId/certificateAuthorities/$CertificateAuthorityName/certificatePolicies/$($PolicyName)?api-version=$($script:AdrApiVersion)"

    Write-Host "Creating ADR root certificate authority ($CertificateAuthorityName-root)"
    Invoke-AzRest -Method PUT -Url $RootUrl -Body @{
        location = $Location
        properties = @{ certificateAuthorityType = "Root"; keyType = "ECC" }
    } | Out-Null
    Wait-AzProvisioningState -Url $RootUrl -Step "ADR root certificate authority"

    Write-Host "Creating ADR issuing certificate authority ($CertificateAuthorityName)"
    Invoke-AzRest -Method PUT -Url $IcaUrl -Body @{
        location = $Location
        properties = @{
            certificateAuthorityType = "ICA"
            keyType = "ECC"
            issuer = @{
                issuerType = "Microsoft"
                certificateAuthorityResourceId = "$NamespaceId/certificateAuthorities/$CertificateAuthorityName-root"
            }
        }
    } | Out-Null
    Wait-AzProvisioningState -Url $IcaUrl -Step "ADR issuing certificate authority"

    Write-Host "Creating ADR certificate policy ($PolicyName)"
    Invoke-AzRest -Method PUT -Url $PolicyUrl -Body @{
        location = $Location
        properties = @{ certificate = @{ validityPeriodInDays = $LeafValidityDays } }
    } | Out-Null
    Wait-AzProvisioningState -Url $PolicyUrl -Step "ADR certificate policy"

    return $CertificateAuthorityName
}

function Sync-DpsAdrConfiguration {
    <#
    .SYNOPSIS
    Forces the DPS data plane to pick up the ADR namespace it has just been linked to.

    .DESCRIPTION
    WORKAROUND. Committing an ADR link records it in the DPS resource provider but does not push the
    DPS scale-unit configuration, so the data plane never learns about the namespace and every
    enrollment write fails with errorCode 400004 ("A Device Registry Namespace is required to be set
    on this DPS instance"). Re-running the DPS update path does push that configuration, and a
    tags-only update is the most benign way to trigger it.

    Best effort by design: the push is asynchronous, so the data plane can converge even when the
    control-plane update times out settling, and enrollment creation waits that window out on its
    own. Remove once the DPS resource provider pushes configuration when a link commits.
    #>
    param(
        [string]$DpsId,
        # Chooses the ARM host, so it must match the location the DPS was created in.
        [string]$Location
    )

    $Url = "$(Get-DpsArmHost -Location $Location)$($DpsId)?api-version=$($script:DpsControlPlaneApiVersion)"

    Write-Host "Pushing the linked ADR namespace into the DPS data plane (tags-only update)."
    try {
        # Guarded because the DPS is created without tags: piping a null property into ForEach-Object
        # still runs the body once, with a null key, which would fail the sync before it is attempted.
        $Dps = Invoke-AzRest -Url $Url
        $Tags = @{}
        if ($null -ne $Dps.tags) { $Dps.tags.PSObject.Properties | %{ $Tags[$_.Name] = $_.Value } }
        $Tags["AdrDataplaneSyncUtc"] = (Get-Date).ToUniversalTime().ToString("o")

        # Retried: enrollment creation retries only the enrollment PUT, so a push that never lands
        # leaves every one of those attempts failing 400004 with nothing to repair it.
        Invoke-WithRetry -Step "Push the linked ADR namespace into the DPS data plane" -ThrowOnFailure `
            -RetryOnPattern $script:ArmTransientPattern -MaxAttempts 3 -InitialDelaySeconds 15 -Command {
            Invoke-AzRest -Method PATCH -Url $Url -Body @{ tags = $Tags }
        } | Out-Null
        Wait-AzProvisioningState -Url $Url -Step "DPS ADR configuration push" -TimeoutSeconds 300
    }
    catch {
        Write-Host "DPS ADR configuration push did not settle cleanly ($($_.Exception.Message)); continuing, as enrollment creation waits for the data plane anyway."
    }
}

# <[Azure DPS Helper Functions]>

function New-DpsDerivedSymmetricKey {
    param(
        $SymmetricKey = $null,
        $DeviceId = $null
    )

    $hmacsha256 = New-Object System.Security.Cryptography.HMACSHA256
    try {
        $hmacsha256.key = [Convert]::FromBase64String($SymmetricKey)
        $sig = $hmacsha256.ComputeHash([Text.Encoding]::ASCII.GetBytes($DeviceId))
        return [Convert]::ToBase64String($sig)
    } finally {
        $hmacsha256.Dispose()
    }
}


function Add-DpsCertificate {
    param(
        [string]$ResourceGroup,
        [string]$DpsName,
        [string]$Subject = $null,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$IssuerCert = $null,
        [System.Security.Cryptography.RSA]$IssuerKey = $null,
        [timespan]$Expiration = $DefaultCertificateExpiration
    )

    if ([string]::IsNullOrWhiteSpace($Subject)) {
        $Subject = "Azure IoT Test Certificate {0}" -f (New-GuidString)
    }

    $DpsCertificateName = $Subject.Replace(" ", "-")
    $Subject = "CN=$Subject"

    Write-Host "Running Add-DpsCertificate($DpsCertificateName)"

    $PrivateKey = New-RsaPrivateKey
    # az iot dps validates certificate files by name: only .pem and .cer are accepted.
    $CertificatePath =  New-TempFile -Extension "pem"
    $Certificate = New-Certificate -Subject $Subject -Key $PrivateKey -IssuerCert $IssuerCert -IssuerKey $IssuerKey -IsCA $true -Days $Expiration.TotalDays -OutFile $CertificatePath

    az iot dps certificate create --dps-name $DpsName --resource-group $ResourceGroup --name $DpsCertificateName --path $CertificatePath | Out-Null
    Stop-OnError -Step "az iot dps certificate create"

    Remove-Item $CertificatePath

    $etag = az iot dps certificate show --dps-name $DpsName --resource-group $ResourceGroup --name $DpsCertificateName --query etag -o tsv
    Stop-OnError -Step "az iot dps certificate show"

    $DpsVerificationCodeInfo = az iot dps certificate generate-verification-code --dps-name $DpsName --resource-group $ResourceGroup --name $DpsCertificateName --etag $etag | ConvertFrom-Json
    Stop-OnError -Step "az iot dps certificate generate-verification-code"

    # Create verification cert
    # az iot dps validates certificate files by name: only .pem and .cer are accepted.
    $DpsVerificationCertificatePath = New-TempFile -Extension "pem"
    $DpsVerificationCertificateSubject = "CN=$($DpsVerificationCodeInfo.properties.verificationCode)"

    $DpsVerificationKey = New-RsaPrivateKey
    New-Certificate -Subject $DpsVerificationCertificateSubject -Key $DpsVerificationKey -IssuerCert $Certificate -IssuerKey $PrivateKey -IsCA $false -Days $Expiration.TotalDays -OutFile $DpsVerificationCertificatePath | Out-Null

    # Verify with DPS
    $etag = az iot dps certificate show --dps-name $DpsName --resource-group $ResourceGroup --name $DpsCertificateName --query etag -o tsv
    Stop-OnError -Step "az iot dps certificate show"

    az iot dps certificate verify --dps-name $DpsName --resource-group $ResourceGroup --name $DpsCertificateName --path $DpsVerificationCertificatePath --etag $etag | Out-Null
    Stop-OnError -Step "az iot dps certificate verify"

    Remove-Item $DpsVerificationCertificatePath

    return [X509CertificateInfo]::new($PrivateKey, $Certificate)
}

function New-DpsServiceSasToken {
    <#
    .SYNOPSIS
    Builds a SharedAccessSignature for the DPS service API from a DPS connection string.
    #>
    param(
        [string]$ConnectionString,
        [int]$TtlSeconds = 3600
    )

    $Parts = @{}
    $ConnectionString.Split(';') | ?{ $_ -match '=' } | %{
        $Name, $Value = $_.Split('=', 2)
        $Parts[$Name] = $Value
    }

    $ServiceHost = $Parts["HostName"]
    $Expiry = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + $TtlSeconds

    $Hmac = New-Object System.Security.Cryptography.HMACSHA256
    try {
        $Hmac.Key = [Convert]::FromBase64String($Parts["SharedAccessKey"])
        $Signature = [Convert]::ToBase64String($Hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes("$ServiceHost`n$Expiry")))
    } finally {
        $Hmac.Dispose()
    }

    return "SharedAccessSignature sr=$([uri]::EscapeDataString($ServiceHost))&sig=$([uri]::EscapeDataString($Signature))&se=$Expiry&skn=$([uri]::EscapeDataString($Parts['SharedAccessKeyName']))"
}

function Set-DpsEnrollment {
    <#
    .SYNOPSIS
    Creates or updates a DPS enrollment through the DPS service API, and returns it.

    .DESCRIPTION
    Enrollments are written over REST rather than with 'az iot dps enrollment[-group] create' because
    the CLI cannot express the ADR certificate policy reference any more: it only ever offered the
    public-preview '--credential-policy', and the property that replaced it is a set of three names
    (see Add-AdrPolicyReference).

    The first enrollment written after a DPS is linked to an ADR namespace commonly fails while the
    link propagates, in two distinct ways, both of which clear on their own:

      403000  the DPS identity's Device Registry grant has not replicated yet;
      400004  the DPS data plane has not picked up the linked namespace yet.

    Both are retried. Any other failure is a real error and is surfaced immediately.

    DPS also returns 400004 for an api-version it does not support, which no amount of waiting
    fixes, so that case is excluded from the retry and fails on the first attempt.

    .PARAMETER Collection
    'enrollmentGroups' for a group enrollment, 'enrollments' for an individual one.
    #>
    param(
        [string]$ResourceGroup,
        [string]$DpsName,
        [ValidateSet("enrollmentGroups", "enrollments")][string]$Collection,
        [string]$EnrollmentId,
        [Hashtable]$Body
    )

    $ConnectionString = az iot dps connection-string show -g $ResourceGroup -n $DpsName --kt primary --pn provisioningserviceowner --query connectionString -o tsv
    Stop-OnError -Step "Get DPS connection string ($DpsName)"

    $ServiceHost = ($ConnectionString.Split(';') | ?{ $_ -like "HostName=*" }).Split('=', 2)[1]
    $Url = "https://$ServiceHost/$Collection/$([uri]::EscapeDataString($EnrollmentId))?api-version=$($script:DpsEnrollmentApiVersion)"
    $Headers = @(
        "Authorization=$(New-DpsServiceSasToken -ConnectionString $ConnectionString)",
        "Content-Type=application/json"
    )

    return Invoke-WithRetry -Step "Create DPS enrollment ($EnrollmentId)" `
        -RetryOnPattern '403000|400004' -StopOnPattern 'Unsupported API version' `
        -MaxAttempts 8 -InitialDelaySeconds 15 -Command {
        $BodyFile = New-TempFile
        try {
            Set-FileContent -Path $BodyFile -Content ($Body | ConvertTo-Json -Compress -Depth 10)
            az rest --method PUT --url $Url --body "@$BodyFile" --headers $Headers `
                --skip-authorization-header --only-show-errors | ConvertFrom-Json
        }
        finally {
            Remove-Item -Path $BodyFile -ErrorAction SilentlyContinue
        }
    }
}

function Add-AdrPolicyReference {
    <#
    .SYNOPSIS
    Adds the ADR certificate policy reference to an enrollment body, if one was supplied.

    .DESCRIPTION
    Public preview referenced the policy by a single name. It is now addressed by three, which have
    to travel together -- a partial reference is rejected -- so an incomplete one is treated the same
    as no reference at all and the enrollment is written without certificate management.

    Note the certificate authority named here is the ISSUING CA, never the root it chains up to.
    #>
    param(
        [Hashtable]$Body,
        [AdrPolicyReference]$AdrPolicy
    )

    if ($null -ne $AdrPolicy -and $AdrPolicy.IsComplete()) {
        $Body["namespaceName"] = $AdrPolicy.NamespaceName
        $Body["certificateAuthorityName"] = $AdrPolicy.CertificateAuthorityName
        $Body["certificatePolicyName"] = $AdrPolicy.CertificatePolicyName
    }

    return $Body
}

function Add-DpsSymmetricKeyIndividualEnrollment {
    param(
        [string]$ResourceGroup = $null,
        [string]$DpsName = $null,
        [string]$EnrollmentId = $null,
        [AdrPolicyReference]$AdrPolicy = $null
    )

    Write-Host "Creating Azure DPS symmetric-key individual enrollment ($EnrollmentId)."

    if ($null -eq $AdrPolicy -or -not $AdrPolicy.IsComplete()) {
        $EnrollmentInfo = az iot dps enrollment create --dps-name $DpsName --resource-group $ResourceGroup --at symmetricKey --enrollment-id $EnrollmentId | ConvertFrom-Json
        Stop-OnError -Step "Create an Azure DPS symmetric-key individual enrollment ($EnrollmentId)"
    } else {
        $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
            registrationId = $EnrollmentId
            attestation = @{ type = "symmetricKey" }
            provisioningStatus = "enabled"
        }

        $EnrollmentInfo = Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollments" -EnrollmentId $EnrollmentId -Body $Body
    }

    return [DpsSymmetricKeyIndividualEnrollmentInfo]::new(
        $EnrollmentId,
        $EnrollmentInfo.attestation.symmetricKey.primaryKey,
        $EnrollmentInfo.attestation.symmetricKey.secondaryKey
    )
}

function Add-DpsX509IndividualEnrollment {
    param(
        [string]$ResourceGroup = $null,
        [string]$DpsName = $null,
        [string]$EnrollmentId = $null,
        [AdrPolicyReference]$AdrPolicy = $null,
        [timespan]$CertificateExpiration = $DefaultCertificateExpiration
    )

    Write-Host "Creating Azure DPS x509 individual enrollment ($EnrollmentId; $CertificateExpiration)."

    $DpsDevicePrivateKey = New-RsaPrivateKey
    $DpsDeviceCertificate = New-Certificate -Subject "CN=$EnrollmentId" -Key $DpsDevicePrivateKey -IssuerCert $null -IssuerKey $null -IsCA $false -Days $CertificateExpiration.TotalDays

    if ($null -eq $AdrPolicy -or -not $AdrPolicy.IsComplete()) {
        # az iot dps validates certificate files by name: only .pem and .cer are accepted.
        $DpsDeviceCertificatePath = New-TempFile -Extension "pem"
        try {
            Export-X509CertificateToPemFile -Cert $DpsDeviceCertificate -Path $DpsDeviceCertificatePath
            az iot dps enrollment create --dps-name $DpsName --resource-group $ResourceGroup --at x509 --enrollment-id $EnrollmentId --cp $DpsDeviceCertificatePath | Out-Null
            Stop-OnError -Step "Create an Azure DPS x509 individual enrollment ($EnrollmentId)"
        }
        finally {
            Remove-Item -Path $DpsDeviceCertificatePath -ErrorAction SilentlyContinue
        }
    } else {
        # An individual x509 enrollment pins the device's own certificate, so the certificate travels
        # in the request body rather than as a file path an 'az' command reads.
        $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
            registrationId = $EnrollmentId
            attestation = @{
                type = "x509"
                x509 = @{ clientCertificates = @{ primary = @{ certificate = [Convert]::ToBase64String($DpsDeviceCertificate.RawData) } } }
            }
            provisioningStatus = "enabled"
        }

        Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollments" -EnrollmentId $EnrollmentId -Body $Body | Out-Null
    }

    return [DpsX509IndividualEnrollmentInfo]::new(
        $EnrollmentId,
        [X509CertificateInfo]::new($DpsDevicePrivateKey, $DpsDeviceCertificate)
    )
}

function Add-DpsSymmetricKeyEnrollmentGroup {
    param(
        [string]$ResourceGroup = $null,
        [string]$DpsName = $null,
        [string]$EnrollmentId = $null,
        [AdrPolicyReference]$AdrPolicy = $null
    )

    Write-Host "Creating Azure DPS symmetric-key enrollment group ($EnrollmentId)."

    if ($null -eq $AdrPolicy -or -not $AdrPolicy.IsComplete()) {
        $EnrollmentInfo = az iot dps enrollment-group create --dps-name $DpsName --resource-group $ResourceGroup --enrollment-id $EnrollmentId | ConvertFrom-Json
        Stop-OnError -Step "Create an Azure DPS symmetric-key enrollment group ($EnrollmentId)"
    } else {
        $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
            enrollmentGroupId = $EnrollmentId
            attestation = @{ type = "symmetricKey" }
            provisioningStatus = "enabled"
        }

        $EnrollmentInfo = Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollmentGroups" -EnrollmentId $EnrollmentId -Body $Body
    }

    return [DpsSymmetricKeyEnrollmentGroupInfo]::new(
        $EnrollmentId,
        $EnrollmentInfo.attestation.symmetricKey.primaryKey,
        $EnrollmentInfo.attestation.symmetricKey.secondaryKey
    )
}

function Add-DpsX509EnrollmentGroup {
    param(
        [string]$ResourceGroup = $null,
        [string]$DpsName = $null,
        [string]$EnrollmentId = $null,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$IssuerCertificate = $null,
        [System.Security.Cryptography.RSA]$IssuerPrivateKey = $null,
        [string]$IotHubFqdn = $null,
        [AdrPolicyReference]$AdrPolicy = $null,
        [timespan]$CertificateExpiration = $DefaultCertificateExpiration
    )

    Write-Host "Creating Azure DPS x509 enrollment group ($EnrollmentId)."

    # The group's signing CA still has to be uploaded to DPS and proved possession of: a device in a
    # group enrollment presents a chain, and DPS validates it against a CA it has verified.
    $ICA = Add-DpsCertificate -ResourceGroup $ResourceGroup -DpsName $DpsName -Subject $EnrollmentId -IssuerCert $IssuerCertificate -IssuerKey $IssuerPrivateKey -Expiration $CertificateExpiration

    if ($null -eq $AdrPolicy -or -not $AdrPolicy.IsComplete()) {
        # az iot dps validates certificate files by name: only .pem and .cer are accepted.
        $ICACertificatePath = New-TempFile -Extension "pem"
        try {
            $ICA.ExportToPemFile($ICACertificatePath)
            az iot dps enrollment-group create --dps-name $DpsName --resource-group $ResourceGroup --enrollment-id $EnrollmentId --ap static --cp $ICACertificatePath --provisioning-status enabled --iot-hubs $IotHubFqdn | Out-Null
            Stop-OnError -Step "Create an Azure DPS x509 enrollment group ($EnrollmentId)"
        }
        finally {
            Remove-Item -Path $ICACertificatePath -ErrorAction SilentlyContinue
        }
    } else {
        $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
            enrollmentGroupId = $EnrollmentId
            attestation = @{
                type = "x509"
                x509 = @{ caReferences = @{ primary = $EnrollmentId.Replace(" ", "-") } }
            }
            provisioningStatus = "enabled"
            allocationPolicy = "static"
            iotHubs = @($IotHubFqdn)
        }

        Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollmentGroups" -EnrollmentId $EnrollmentId -Body $Body | Out-Null
    }

    return [DpsX509EnrollmentGroupInfo]::new($EnrollmentId, $ICA)
}
