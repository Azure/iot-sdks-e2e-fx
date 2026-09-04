[TimeSpan]$DefaultCertificateExpiration = [TimeSpan]::FromDays(365)

# This script is divided by sections, tagged as # <[Section Name]>.
# The sections are:
# - Generic Helper Functions
# - Certificate Handling
# - Generic Types
# - Azure IoT Types
# - Azure DPS Helper Functions
# - Azure DevOps
# - Azure IoT Test Environment Public Functions


# <[Generic Helper Functions]>
function Debug-PSScript {
    param($Path)

    $Path = Resolve-Path $Path

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null

    $errors | ForEach-Object {
        [pscustomobject]@{
            Message = $_.Message
            File    = $_.Extent.File
            Line    = $_.Extent.StartLineNumber
            Column  = $_.Extent.StartColumnNumber
            Text    = $_.Extent.Text
        }
    } | Format-List
}

function Invoke-Script {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [scriptblock] $ScriptBlock
    )

    try {
        & $ScriptBlock
    }
    catch {
        Write-Host "Exception: $($_.ToString())"
        Write-Host "Errors:"
        $_.InvocationInfo
        $null
    }
}

function New-GuidString {
    param(
        [switch]$NoDashes,
        [int]$MaxLength = 0
    )

    $Guid = [guid]::NewGuid().ToString()

    if ($NoDashes) {
        $Guid = $Guid.Replace('-', '')
    }

    if ($MaxLength -gt 0 -and $Guid.Length -gt $MaxLength) {
        $Guid = $Guid.Substring(0, $MaxLength)
    }

    return $Guid
}

function New-TempFile {
    # $Extension is the extension WITHOUT the leading dot (e.g. "pem"); a leading
    # dot is tolerated. When omitted, the .tmp path is returned unchanged.
    param([string]$Extension = '')

    # GetTempFileName() guarantees the name it returns is unused, but that
    # guarantee only covers the .tmp file it creates: replacing the extension can
    # land on a name another process already owns. Retry until the final path is
    # free so the caller still gets a unique file.
    $MaxAttempts = 10

    for ($Attempt = 0; $Attempt -lt $MaxAttempts; $Attempt++) {
        $TempFilePath = [System.IO.Path]::GetTempFileName()
        Remove-Item -Path $TempFilePath

        if ([string]::IsNullOrEmpty($Extension)) {
            break
        }

        $Suffix = if ($Extension.StartsWith('.')) { $Extension } else { ".$Extension" }
        $TempFilePath = [System.IO.Path]::ChangeExtension($TempFilePath, $Suffix)

        if (-not (Test-Path $TempFilePath)) {
            break
        }
    }

    return $TempFilePath
}

function ConvertTo-Base64 {
    param($Content)
    $ContentBytes  = [System.Text.Encoding]::UTF8.GetBytes($Content)
    $Base64Content = [System.Convert]::ToBase64String($ContentBytes)
    return $Base64Content
}

function Set-FileContent {
    param(
        $Path = $null,
        $Content = $null
    )

    $OutFileDir = Split-Path -Path $Path -Parent
    if ($OutFileDir -ne "" -and $(Test-Path $OutFileDir) -eq $false) {
        New-Item -ItemType Directory -Force -Path $OutFileDir | Out-Null        
    }

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)  # $false = no BOM
        [System.IO.File]::WriteAllText("$Path", "$Content", $Utf8NoBom)
    } else {
        Set-Content -Path "$Path" -Value $Content -Encoding utf8 -NoNewline
    }
}

function Stop-OnError {
    param([string]$Step = 'Command', [int]$ExpectedReturn = 0, [switch]$Throw)
    if ($LASTEXITCODE -ne $ExpectedReturn) {
        $ErrorMessage = "ERROR: `"$Step`" failed (exit code $LASTEXITCODE)"
        if ($Throw) {
            throw $ErrorMessage
        } else {
            Write-Host $ErrorMessage 
            exit 1
        }
    }
}

# The azure-iot CLI extension is used for IoT Hub and DPS resource management only.
#
# It is deliberately NOT pinned any more. The pin existed because provisioning
# needed the `az iot adr` command group, which only ever shipped in preview
# builds. That command group models ADR the way public preview did -- a
# namespace credential holding policies, referenced from an enrollment by name --
# and that model has since been replaced (see New-AdrCertificateAuthority). The
# extension has no command for the model that replaced it, so every ADR call
# here goes to ARM directly via `az rest` and the pin buys nothing.
#
# Nothing here depends on a preview build: the ADR resources are created through
# ARM, and so is the DPS system-assigned identity, whose creation-time flags are
# preview-only. What IS installed still has to be current, though -- an agent
# carrying an old extension would otherwise keep it forever -- so an extension
# that is already present is updated rather than left alone.
function Install-AzureIotCliExtension {
    $Extension = $(az extension list --output json --only-show-errors | ConvertFrom-Json | ?{$_.name -eq "azure-iot"})

    if ($null -eq $Extension) {
        Write-Host "Installing Azure IoT extension."
        az extension add --name azure-iot --only-show-errors | Out-Null
        Stop-OnError -Step "Install Azure IoT extension"
    } else {
        # No suppression here: the command succeeds when the extension is already current, so a
        # failure is a real one and worth stopping for.
        Write-Host "Azure IoT extension $($Extension.version) found; updating."
        az extension update --name azure-iot --only-show-errors | Out-Null
        Stop-OnError -Step "Update Azure IoT extension"
    }

    # What actually ended up installed. When a provisioning command goes missing,
    # this is the first thing worth seeing in the log.
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

function Invoke-AzRest {
    <#
    .SYNOPSIS
    Calls an ARM endpoint with `az rest`, passing the body as a file, and returns parsed JSON.

    .DESCRIPTION
    `az rest --body` only reliably carries JSON when it is handed a file: under the AzureCLI@2
    task an inline body is re-quoted by the shell and arrives malformed. Every ARM call in this
    module therefore writes a temp file first, and this collapses that boilerplate into one place.

    .PARAMETER Method
    HTTP method. Defaults to GET, which takes no body.

    .PARAMETER Url
    Fully-qualified ARM URL, including the api-version query parameter.

    .PARAMETER Body
    Request payload as a hashtable. Serialized to JSON; omit for GET.

    .PARAMETER AllowFailure
    Return $null instead of stopping when the call fails. Used for existence and state probes, where
    a failure is an answer rather than an error; stderr is suppressed in that case only, so that
    callers wrapping this in Invoke-WithRetry can still see -- and match on -- a real error.
    #>
    param(
        [string]$Method = "GET",
        [Parameter(Mandatory = $true)][string]$Url,
        [Hashtable]$Body = $null,
        [switch]$AllowFailure
    )

    $BodyFile = $null
    try {
        $Arguments = @("rest", "--method", $Method, "--url", $Url, "--only-show-errors")

        if ($null -ne $Body) {
            $BodyFile = New-TempFile
            Set-FileContent -Path $BodyFile -Content ($Body | ConvertTo-Json -Compress -Depth 10)
            $Arguments += @("--body", "@$BodyFile")
        }

        if ($AllowFailure) {
            $Response = az @Arguments 2>$null
            if ($LASTEXITCODE -ne 0) {
                $global:LASTEXITCODE = 0
                return $null
            }
        } else {
            $Response = az @Arguments
            if ($LASTEXITCODE -ne 0) {
                # Throws rather than exits, so a call wrapped in Invoke-WithRetry can be retried;
                # an unhandled throw still fails the run for every other caller.
                Stop-OnError -Step "$Method $Url" -Throw
            }
        }

        if ([string]::IsNullOrWhiteSpace($Response)) {
            return $null
        }

        return $Response | ConvertFrom-Json
    }
    finally {
        if ($null -ne $BodyFile) {
            Remove-Item -Path $BodyFile -ErrorAction SilentlyContinue
        }
    }
}

function Wait-AzProvisioningState {
    <#
    .SYNOPSIS
    Polls an ARM resource until its provisioningState is terminal, and throws unless it succeeded.

    .DESCRIPTION
    The ADR resources created here (namespace, certificate authorities, certificate policy) are
    provisioned asynchronously: the PUT returns immediately and the outcome only shows up in
    provisioningState. Creating a child before its parent is Succeeded fails, so each create waits.

    .PARAMETER Url
    ARM URL of the resource, including api-version.

    .PARAMETER Step
    Human-readable name of the resource, used in progress and error messages.

    .PARAMETER TimeoutSeconds
    How long to wait for a terminal state before giving up.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Step,
        [int]$TimeoutSeconds = 600
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ($true) {
        # A failed read is deliberately not fatal: these resources are polled for minutes, and a
        # transient ARM or CLI failure along the way says nothing about the provisioning itself.
        # The state is simply unknown for this attempt, and the deadline still applies.
        $Resource = Invoke-AzRest -Url $Url -AllowFailure
        $State = if ($null -ne $Resource) { $Resource.properties.provisioningState } else { $null }

        if ($State -eq "Succeeded") {
            return
        }

        if ($State -eq "Failed" -or $State -eq "Canceled") {
            throw "$Step reached provisioningState '$State'."
        }

        if ((Get-Date) -ge $Deadline) {
            throw "$Step did not reach a terminal provisioningState within $TimeoutSeconds seconds (last state: '$State')."
        }

        Write-Host "Waiting for $Step (provisioningState=$State)."
        Start-Sleep -Seconds 10
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

function Join-Hashtable {
    param(
        [Hashtable]$Hashtable,
        [string]$Separator = " "
    )

    if ($null -eq $Hashtable -or $Hashtable.Count -eq 0) {
        return ""
    } else {
        return ($Hashtable.GetEnumerator() | %{ "$($_.Key)=$($_.Value)" }) -join $Separator
    }
}

function ConvertTo-TagArguments {
    param([Hashtable]$Hashtable)

    if ($null -eq $Hashtable -or $Hashtable.Count -eq 0) {
        return @()
    }

    return @(
        $Hashtable.GetEnumerator() | ForEach-Object {
            $Key = [string]$_.Key
            $Value = if ($null -eq $_.Value) { "" } else { [string]$_.Value }

            # If callers already include wrapping double quotes, normalize it to a raw value.
            if ($Value.Length -ge 2 -and $Value.StartsWith('"') -and $Value.EndsWith('"')) {
                $Value = $Value.Substring(1, $Value.Length - 2)
            }

            "$Key=$Value"
        }
    )
}

function Convert-CollectionToHashtable {
    param([array]$Collection)
    if ($null -eq $Collection) { return @() }
    return @(foreach ($item in $Collection) { if ($null -ne $item) { $item.ToHashtable() } })
}

function ConvertTo-Hashtable {
    param($Object)
    if ($null -ne $Object) {
        return $Object.ToHashtable()
    } else {
        return $null
    }
}

function ConvertFrom-PSObject {
    param($Object)
    if ($Object -is [System.Management.Automation.PSCustomObject]) {
        $Hashtable = [ordered]@{}
        foreach ($Property in $Object.PSObject.Properties) {
            $Hashtable[$Property.Name] = ConvertFrom-PSObject $Property.Value
        }
        return $Hashtable
    } elseif ($Object -is [System.Collections.IEnumerable] -and $Object -isnot [string]) {
        return @(foreach ($Item in $Object) { ConvertFrom-PSObject $Item })
    } else {
        return $Object
    }
}

function New-RandomNumber {
    param($Length = 16)

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $RandomNumber = New-Object byte[] $Length
        [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($RandomNumber)
        return $RandomNumber
    } else {
        return [System.Security.Cryptography.RandomNumberGenerator]::GetBytes($Length)
    }
}


# <[Certificate Handling]>

function Export-Pkcs8PrivateKeyPem {
    param($Key) 
    # Key of type [System.Security.Cryptography.RSA] or [System.Security.Cryptography.ECDsa]

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $KeyPemHex = [Convert]::ToBase64String($Key.Key.Export([System.Security.Cryptography.CngKeyBlobFormat]::Pkcs8PrivateBlob), 'InsertLineBreaks')
        return "-----BEGIN PRIVATE KEY-----`n$KeyPemHex`n-----END PRIVATE KEY-----"
    } else {
        return $Key.ExportPkcs8PrivateKeyPem()
    }
}

function Export-RsaPkcs1PrivateKeyPem {
    param([System.Security.Cryptography.RSA]$Key)

    try {
        if ($PSVersionTable.PSVersion.Major -lt 7) {
            throw "ExportRSAPrivateKeyPem is unavailable"
        }

        return $Key.ExportRSAPrivateKeyPem()
    }
    catch {
        # Fallback for older runtimes; PKCS8 is still accepted by non-Schannel paths.
        return Export-Pkcs8PrivateKeyPem -Key $Key
    }
}

function New-RsaKeyFromPem {
    param([string]$Pem)

    $rsa = [System.Security.Cryptography.RSA]::Create()

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $Base64 = ($Pem -replace "-----BEGIN PRIVATE KEY-----", "" -replace "-----END PRIVATE KEY-----", "").Trim() -replace "\s+", ""
        $KeyBytes = [Convert]::FromBase64String($Base64)
        $bytesRead = 0
        $rsa.ImportPkcs8PrivateKey($KeyBytes, [ref]$bytesRead)
    } else {
        $rsa.ImportFromPem($Pem)
    }

    return $rsa
}

function New-RsaPrivateKey {
    param(
        [string]$Path = $null,
        [switch]$Verbose
    )

    $rsa = [System.Security.Cryptography.RSA]::Create(4096)

    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        $pem = Export-Pkcs8PrivateKeyPem -Key $rsa

        if ($Verbose) {
            Write-Host "Saving private key to $Path"
        }

        Set-FileContent -Path $Path -Content $pem
    }

    return $rsa
}

function New-EcdsaPrivateKey {
    param(
        [string]$Curve = "nistP256",
        [string]$Path = $null,
        [switch]$Verbose
    )

    $ecdsa = [System.Security.Cryptography.ECDsa]::Create([System.Security.Cryptography.ECCurve]::CreateFromFriendlyName($Curve))

    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        $pem = Export-Pkcs8PrivateKeyPem -Key $ecdsa

        if ($Verbose) {
            Write-Host "Saving ECDSA private key ($Curve) to $Path"
        }

        Set-FileContent -Path $Path -Content $pem
    }

    return $ecdsa
}

function New-X509CertificateSigningRequest {
    param(
        [string]$Subject,
        $Key = $null,
        [System.Security.Cryptography.HashAlgorithmName]$HashAlgorithm = [System.Security.Cryptography.HashAlgorithmName]::SHA256,
        [Switch]$AsBytes,
        [Switch]$NoHeaders
    )

    $DistinguishedName = [System.Security.Cryptography.X509Certificates.X500DistinguishedName]::new("CN=$Subject")
    $csr = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new($DistinguishedName, $Key, $HashAlgorithm)
    
    if ($AsBytes) {
        return $csr.CreateSigningRequest()
    } else {

        if ($NoHeaders) {
            return [Convert]::ToBase64String($csr.CreateSigningRequest())
        } else {
            $Base64Csr = [Convert]::ToBase64String($csr.CreateSigningRequest(), 'InsertLineBreaks')
            return "-----BEGIN CERTIFICATE REQUEST-----`n$Base64Csr`n-----END CERTIFICATE REQUEST-----"
        }
    }
}

function New-Certificate {
    param(
        [string]$Subject,
        [System.Security.Cryptography.RSA]$Key,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$IssuerCert = $null,
        [System.Security.Cryptography.RSA]$IssuerKey = $null,
        [bool]$IsCA = $false,
        [int]$Days = $DefaultCertificateExpiration.TotalDays,
        [string]$OutFile = $null
    )
    Write-Host "Running New-Certificate($Subject)"

    $req = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new($Subject, [System.Security.Cryptography.RSA]$Key, [System.Security.Cryptography.HashAlgorithmName]::SHA256, [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)

    $SubjectKeyIdentifierExtension = [System.Security.Cryptography.X509Certificates.X509SubjectKeyIdentifierExtension]::new($req.PublicKey, $false)
    $req.CertificateExtensions.Add($SubjectKeyIdentifierExtension)

    if ($IsCA) {
        $BasicConstraintExtension = New-Object System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension -ArgumentList $true, $false, 0, $true
        $req.CertificateExtensions.Add($BasicConstraintExtension)
    } else {
        $BasicConstraintExtension = New-Object System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension -ArgumentList $false, $false, 0, $false
        $req.CertificateExtensions.Add($BasicConstraintExtension)
    }

    if ($IsCA) {
        $KeyUsageExtension = [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new( `
            [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature `
            -bor [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::CrlSign `
            -bor [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyCertSign,
            $true)
    } else {
        $KeyUsageExtension = [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new( `
            [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature `
            -bor [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyEncipherment,
            $true)
    }

    $req.CertificateExtensions.Add($KeyUsageExtension)

    if (-not $IsCA) {
        $EkuOids = [System.Security.Cryptography.OidCollection]::new()
        [void]$EkuOids.Add(
            [System.Security.Cryptography.Oid]::new("1.3.6.1.5.5.7.3.2") # clientAuth = 1.3.6.1.5.5.7.3.2
        ) 
        $EnhancedKeyUsageExtension = [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($EkuOids, $false)
        $req.CertificateExtensions.Add($EnhancedKeyUsageExtension)
    }

    $NotBefore = [datetime]::UtcNow
    $NotAfter = [datetime]::UtcNow.AddDays($Days)

    if ($null -eq $IssuerCert) {
        # Self-signed (Root CA)
        $NewCertificate = $req.CreateSelfSigned($NotBefore, $NotAfter)

        if (-not [string]::IsNullOrWhiteSpace($OutFile)) {
            Export-X509CertificateToPemFile -Cert $NewCertificate -Path $OutFile
        }

        return $NewCertificate
    } else {
        # Signed by issuer (Intermediate or Device)

        # Adjust NotBefore and NotAfter to match issuer certificate.
        if ($null -ne $IssuerCert.NotBefore -and $NotBefore -lt $IssuerCert.NotBefore) {
            $NotBefore = $IssuerCert.NotBefore
        }

        if ($null -ne $IssuerCert.NotAfter -and $NotAfter -gt $IssuerCert.NotAfter) {
            $NotAfter = $IssuerCert.NotAfter
        }

        # Serial number must be random bytes (8–20 bytes is typical)
        $SerialNumber = New-RandomNumber -Length 16

        # Use the issuer *private key* for signing
        $SignatureGenerator = [System.Security.Cryptography.X509Certificates.X509SignatureGenerator]::CreateForRSA(
            $IssuerKey,
            [System.Security.Cryptography.RSASignaturePadding]::Pkcs1
        )

        # Use issuer subject name from the issuer cert
        $NewCertificate = $req.Create(
            $IssuerCert.SubjectName,
            $SignatureGenerator,
            $NotBefore,
            $NotAfter,
            $SerialNumber
        )

        if (-not [string]::IsNullOrWhiteSpace($OutFile)) {
            Export-X509CertificateToPemFile -Cert $NewCertificate -Path $OutFile
        }

        return $NewCertificate
    }
}

function Export-X509CertificateToPem {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $CertificatePemHex = [Convert]::ToBase64String($Certificate.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert), 'InsertLineBreaks')
        return "-----BEGIN CERTIFICATE-----`n$CertificatePemHex`n-----END CERTIFICATE-----"
    } else {
        return $Certificate.ExportCertificatePem()
    }
}

function New-X509Certificate2FromPem {
    param([string]$Pem)

    $Base64 = ($Pem -replace "-----BEGIN CERTIFICATE-----", "" -replace "-----END CERTIFICATE-----", "").Trim() -replace "\s+", ""
    $CertBytes = [Convert]::FromBase64String($Base64)

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        return [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($CertBytes)
    } else {
        $Cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new()
        $Cert.ImportFromPem($Pem)
        return $Cert
    }
}

function Export-X509CertificateToPemFile {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert, [string]$Path)
    $pem = Export-X509CertificateToPem -Certificate $Cert
    Write-Host "Exporting certificate to $Path"
    Set-FileContent -Path $Path -Content $pem
}

# <[Generic Types]>
class RsaPrivateKeyInfo {
    [System.Security.Cryptography.RSA]$PrivateKey = $null

    RsaPrivateKeyInfo(
        [System.Security.Cryptography.RSA]$PrivateKey
    ) {
        $this.PrivateKey = $PrivateKey
    }

    [System.Security.Cryptography.RSA]ToNativeRsaKey() {
        return $this.PrivateKey
    }

    [string]ToPem() {
        return Export-Pkcs8PrivateKeyPem -Key $this.PrivateKey
    }

    [string]ToRsaPkcs1Pem() {
        return Export-RsaPkcs1PrivateKeyPem -Key $this.PrivateKey
    }

    [hashtable]ToHashtable() {
        return [ordered]@{
            PrivateKey = $this.ToPem()
        }
    }

    static [RsaPrivateKeyInfo]FromHashtable([hashtable]$Hashtable) {
        if ($null -eq $Hashtable) {
            return $null
        } else {
            return [RsaPrivateKeyInfo]::new($(New-RsaKeyFromPem -Pem $Hashtable.PrivateKey))
        }
    }
}

class X509CertificateInfo {
    [RsaPrivateKeyInfo]$PrivateKey = $null
    [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate = $null

    X509CertificateInfo() { }

    X509CertificateInfo(
        [System.Security.Cryptography.RSA]$PrivateKey,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate
    ) {
        $this.PrivateKey = [RsaPrivateKeyInfo]::new($PrivateKey)
        $this.Certificate = $Certificate
    }

    [string]GetThumbprint() {
        return $this.Certificate.Thumbprint
    }

    [System.Security.Cryptography.X509Certificates.X509Certificate2]ToNativeX509Certificate2() {
        return $this.Certificate
    }

    [string]ToPem() {
        return Export-X509CertificateToPem -Certificate $this.Certificate
    }

    [void]ExportToPemFile([string]$Path) {
        Export-X509CertificateToPemFile -Cert $this.Certificate -Path $Path
    }

    [hashtable]ToHashtable() {
        return [ordered]@{
            PrivateKey = ConvertTo-Hashtable -Object $this.PrivateKey
            Certificate = $this.ToPem()
        }
    }

    static [X509CertificateInfo] FromHashtable([hashtable]$Hashtable) {
        if ($null -eq $Hashtable) {
            return $null
        } else {
            $Instance = [X509CertificateInfo]::new()
            $Instance.PrivateKey = [RsaPrivateKeyInfo]::FromHashtable($Hashtable.PrivateKey)
            $Instance.Certificate = New-X509Certificate2FromPem -Pem $Hashtable.Certificate
            return $Instance
        }
     }
}


# <[Azure IoT Types]>
class IotHubSymmetricKeyIdentityInfo {
    [string]$Id = $null
    [string]$PrimaryKey = $null
    [string]$SecondaryKey = $null
    [string]$PrimaryConnectionString = $null
    [string]$SecondaryConnectionString = $null

    IotHubSymmetricKeyIdentityInfo(
        [string]$Id,
        [string]$PrimaryKey,
        [string]$SecondaryKey,
        [string]$PrimaryConnectionString,
        [string]$SecondaryConnectionString
    ) {
        $this.Id = $Id
        $this.PrimaryKey = $PrimaryKey
        $this.SecondaryKey = $SecondaryKey
        $this.PrimaryConnectionString = $PrimaryConnectionString
        $this.SecondaryConnectionString = $SecondaryConnectionString
    }
    
    [hashtable] ToHashtable() {
        return [ordered]@{
            Id = $this.Id
            PrimaryKey = $this.PrimaryKey
            SecondaryKey = $this.SecondaryKey
            PrimaryConnectionString = $this.PrimaryConnectionString
            SecondaryConnectionString = $this.SecondaryConnectionString
        }
    }

    static [IotHubSymmetricKeyIdentityInfo] FromHashtable([hashtable]$Hashtable) {
        return [IotHubSymmetricKeyIdentityInfo]::new(
            $Hashtable.Id,
            $Hashtable.PrimaryKey,
            $Hashtable.SecondaryKey,
            $Hashtable.PrimaryConnectionString,
            $Hashtable.SecondaryConnectionString
        )
     }
}

class IotHubX509IdentityInfo {
    [string]$Id = $null
    [string]$ConnectionString = $null
    [X509CertificateInfo]$PrimaryCertificate = $null
    [X509CertificateInfo]$SecondaryCertificate = $null

    IotHubX509IdentityInfo(
        [string]$Id,
        [string]$ConnectionString,
        [X509CertificateInfo]$PrimaryCertificate,
        [X509CertificateInfo]$SecondaryCertificate
    ) {
        $this.Id = $Id
        $this.ConnectionString = $ConnectionString
        $this.PrimaryCertificate = $PrimaryCertificate
        $this.SecondaryCertificate = $SecondaryCertificate
    }

    [hashtable] ToHashtable() {
        return [ordered]@{
            Id = $this.Id
            ConnectionString = $this.ConnectionString
            PrimaryCertificate = ConvertTo-Hashtable -Object $this.PrimaryCertificate
            SecondaryCertificate = ConvertTo-Hashtable -Object $this.SecondaryCertificate
        }
    }

    static [IotHubX509IdentityInfo] FromHashtable([hashtable]$Hashtable) {
        $Certificate1 = if ($null -ne $Hashtable.PrimaryCertificate) { [X509CertificateInfo]::FromHashtable($Hashtable.PrimaryCertificate) } else { $null }
        $Certificate2 = if ($null -ne $Hashtable.SecondaryCertificate) { [X509CertificateInfo]::FromHashtable($Hashtable.SecondaryCertificate) } else { $null }

        return [IotHubX509IdentityInfo]::new($Hashtable.Id, $Hashtable.ConnectionString, $Certificate1, $Certificate2)
     }
}

class DpsSymmetricKeyIdentityInfo {
    [string]$Id
    [string]$PrimaryKey
    [string]$SecondaryKey

    DpsSymmetricKeyIdentityInfo() {
        $this.Id = $null
        $this.PrimaryKey = $null
        $this.SecondaryKey = $null
    }

    DpsSymmetricKeyIdentityInfo(
        [string]$Id,
        [string]$PrimaryKey,
        [string]$SecondaryKey
    ) {
        $this.Id = $Id
        $this.PrimaryKey = $PrimaryKey
        $this.SecondaryKey = $SecondaryKey
    }

    [DpsSymmetricKeyIdentityInfo]DeriveKeysForDevice([string]$DeviceId) {
        return [DpsSymmetricKeyIdentityInfo]::new(
            $DeviceId,
            $(New-DpsDerivedSymmetricKey -SymmetricKey $this.PrimaryKey -DeviceId $DeviceId),
            $(New-DpsDerivedSymmetricKey -SymmetricKey $this.SecondaryKey -DeviceId $DeviceId)
        )
    }

    [hashtable] ToHashtable() {
        return [ordered]@{
            Id = $this.Id
            PrimaryKey = $this.PrimaryKey
            SecondaryKey = $this.SecondaryKey
        }
    }

    static [DpsSymmetricKeyIdentityInfo] FromHashtable([hashtable]$Hashtable) {
        return [DpsSymmetricKeyIdentityInfo]::new($Hashtable.Id, $Hashtable.PrimaryKey, $Hashtable.SecondaryKey)
    }
}

class DpsX509IdentityInfo {
    [string]$Id
    [X509CertificateInfo]$Certificate

    DpsX509IdentityInfo(
        [string]$Id,
        [X509CertificateInfo]$Certificate
     ) {
        $this.Id = $Id
        $this.Certificate = $Certificate
     }

    [hashtable] ToHashtable() {
        return [ordered]@{
            Id = $this.Id
            Certificate = $(ConvertTo-Hashtable -Object $this.Certificate)
        }
    }

    static [DpsX509IdentityInfo] FromHashtable([hashtable]$Hashtable) {
        $ParsedCertificate = [X509CertificateInfo]::FromHashtable($Hashtable.Certificate)
        return [DpsX509IdentityInfo]::new($Hashtable.Id, $ParsedCertificate)
     }
}

class DpsSymmetricKeyIndividualEnrollmentInfo : DpsSymmetricKeyIdentityInfo {
    DpsSymmetricKeyIndividualEnrollmentInfo(
        [string]$Id,
        [string]$PrimaryKey,
        [string]$SecondaryKey
    ) : base($Id, $PrimaryKey, $SecondaryKey) { }

    static [DpsSymmetricKeyIndividualEnrollmentInfo] FromHashtable([hashtable]$Hashtable) {
        return [DpsSymmetricKeyIndividualEnrollmentInfo]::new($Hashtable.Id, $Hashtable.PrimaryKey, $Hashtable.SecondaryKey)
    }
}

class DpsX509IndividualEnrollmentInfo : DpsX509IdentityInfo {
    DpsX509IndividualEnrollmentInfo(
        [string]$Id,
        [X509CertificateInfo]$Certificate
     ) : base($Id, $Certificate) { }

    static [DpsX509IndividualEnrollmentInfo] FromHashtable([hashtable]$Hashtable) {
        $ParsedCertificate = if ($null -ne $Hashtable.Certificate) { [X509CertificateInfo]::FromHashtable($Hashtable.Certificate) } else { $null }
        return [DpsX509IndividualEnrollmentInfo]::new($Hashtable.Id, $ParsedCertificate)
    }
}

class DpsSymmetricKeyEnrollmentGroupInfo : DpsSymmetricKeyIdentityInfo {
    [DpsSymmetricKeyIdentityInfo[]]$Identities = @()

    DpsSymmetricKeyEnrollmentGroupInfo(
        [string]$Id,
        [string]$PrimaryKey,
        [string]$SecondaryKey
    ) : base($Id, $PrimaryKey, $SecondaryKey) { }

    [DpsSymmetricKeyIdentityInfo]AddIdentity([string]$DeviceId) {
        $DeviceIdentityInfo = $this.DeriveKeysForDevice($DeviceId)

        $this.Identities += $DeviceIdentityInfo

        return $DeviceIdentityInfo
    }

    [hashtable] ToHashtable() {
        return [ordered]@{
            Id = $this.Id
            PrimaryKey = $this.PrimaryKey
            SecondaryKey = $this.SecondaryKey
            Identities = Convert-CollectionToHashtable -Collection $this.Identities
        }
    }

    static [DpsSymmetricKeyEnrollmentGroupInfo]FromHashtable([hashtable]$Hashtable) {
        $DpsSymmetricKeyEnrollmentGroupInfo = [DpsSymmetricKeyEnrollmentGroupInfo]::new($Hashtable.Id, $Hashtable.PrimaryKey, $Hashtable.SecondaryKey)
        if ($null -ne $Hashtable.Identities) { $DpsSymmetricKeyEnrollmentGroupInfo.Identities = @($Hashtable.Identities | ?{ $null -ne $_ } | %{ [DpsSymmetricKeyIdentityInfo]::FromHashtable($_) }) }
        return $DpsSymmetricKeyEnrollmentGroupInfo
     }
}

class DpsX509EnrollmentGroupInfo : DpsX509IdentityInfo {
    [DpsX509IdentityInfo[]]$Identities = @()

    DpsX509EnrollmentGroupInfo() { }

    DpsX509EnrollmentGroupInfo(
        [string]$Id,
        [X509CertificateInfo]$Certificate
     ) : base($Id, $Certificate) { }

     [DpsX509IdentityInfo]AddIdentity([string]$DeviceId, [timespan]$CertificateExpiration) {
        $EnrollmentGroupPrivateKey = $this.Certificate.PrivateKey.ToNativeRsaKey()
        $EnrollmentGroupCertificate = $this.Certificate.ToNativeX509Certificate2()

        $DpsDevicePrivateKey = New-RsaPrivateKey
        $DpsDeviceCertificate = New-Certificate -Subject "CN=$DeviceId" -Key $DpsDevicePrivateKey -IssuerCert $EnrollmentGroupCertificate -IssuerKey $EnrollmentGroupPrivateKey -IsCA $false -Days $CertificateExpiration.TotalDays

        $DeviceIdentityInfo = [DpsX509IdentityInfo]::new(
            $DeviceId,
            [X509CertificateInfo]::new($DpsDevicePrivateKey, $DpsDeviceCertificate)
        )

        $this.Identities += $DeviceIdentityInfo

        return $DeviceIdentityInfo
     }

     [hashtable] ToHashtable() {
        return [ordered]@{
            Id = $this.Id
            Certificate = ConvertTo-Hashtable -Object $this.Certificate
            Identities = Convert-CollectionToHashtable -Collection $this.Identities
        }
     }

     static [DpsX509EnrollmentGroupInfo]FromHashtable([hashtable]$Hashtable) {
        $Certificate = [X509CertificateInfo]::FromHashtable($Hashtable.Certificate)
        $DpsX509EnrollmentGroupInfo = [DpsX509EnrollmentGroupInfo]::new($Hashtable.Id, $Certificate)
        if ($null -ne $Hashtable.Identities) { $DpsX509EnrollmentGroupInfo.Identities = @($Hashtable.Identities | ?{ $null -ne $_ } | %{ [DpsX509IdentityInfo]::FromHashtable($_) }) }
        return $DpsX509EnrollmentGroupInfo
     }

}

class DpsEnrollmentsSet {
    [DpsSymmetricKeyIndividualEnrollmentInfo[]]$IndividualSymmetricKey = [DpsSymmetricKeyIndividualEnrollmentInfo[]]@()
    [DpsX509IndividualEnrollmentInfo[]]$IndividualX509 = [DpsX509IndividualEnrollmentInfo[]]@()
    [DpsSymmetricKeyEnrollmentGroupInfo[]]$GroupSymmetricKey = [DpsSymmetricKeyEnrollmentGroupInfo[]]@()
    [DpsX509EnrollmentGroupInfo[]]$GroupX509 = [DpsX509EnrollmentGroupInfo[]]@()

    DpsEnrollmentsSet() { }

    [hashtable]ToHashtable() {
        return [ordered]@{
            IndividualSymmetricKey = Convert-CollectionToHashtable -Collection $this.IndividualSymmetricKey
            IndividualX509 = Convert-CollectionToHashtable -Collection $this.IndividualX509
            GroupSymmetricKey = Convert-CollectionToHashtable -Collection $this.GroupSymmetricKey
            GroupX509 = Convert-CollectionToHashtable -Collection $this.GroupX509
        }
    }

    static [DpsEnrollmentsSet]FromHashtable([hashtable]$Hashtable) {
        $DpsEnrollmentsSet = [DpsEnrollmentsSet]::new()
        if ($null -ne $Hashtable.IndividualSymmetricKey) {
            foreach ($Enrollment in $Hashtable.IndividualSymmetricKey) {
                if ($null -ne $Enrollment) {
                    $IndividualSymmetricKeyEnrollment = [DpsSymmetricKeyIndividualEnrollmentInfo]::FromHashtable($Enrollment)
                    $DpsEnrollmentsSet.IndividualSymmetricKey += $IndividualSymmetricKeyEnrollment
                }
            }
        }
        if ($null -ne $Hashtable.IndividualX509) { $DpsEnrollmentsSet.IndividualX509 = @($Hashtable.IndividualX509 | ?{ $null -ne $_ } | %{ [DpsX509IndividualEnrollmentInfo]::FromHashtable($_) }) }
        if ($null -ne $Hashtable.GroupSymmetricKey) { $DpsEnrollmentsSet.GroupSymmetricKey = @($Hashtable.GroupSymmetricKey | ?{ $null -ne $_ } | %{ [DpsSymmetricKeyEnrollmentGroupInfo]::FromHashtable($_) }) }
        if ($null -ne $Hashtable.GroupX509) { $DpsEnrollmentsSet.GroupX509 = @($Hashtable.GroupX509 | ?{ $null -ne $_ } | %{ [DpsX509EnrollmentGroupInfo]::FromHashtable($_) }) }
        return $DpsEnrollmentsSet
     }
}

class AdrPolicyReference {
    <#
    Identifies the ADR certificate policy an enrollment issues device certificates from.

    Public preview identified it with a single name ('credentialPolicyName'). It is now addressed by
    the three names below, which enrollments must carry together -- a partial reference is not a
    weaker reference, it is an invalid one -- so IsComplete() gates every use of it.
    #>
    [string]$NamespaceName = $null
    [string]$CertificateAuthorityName = $null
    [string]$CertificatePolicyName = $null

    AdrPolicyReference() { }

    AdrPolicyReference([string]$NamespaceName, [string]$CertificateAuthorityName, [string]$CertificatePolicyName) {
        $this.NamespaceName = $NamespaceName
        $this.CertificateAuthorityName = $CertificateAuthorityName
        $this.CertificatePolicyName = $CertificatePolicyName
    }

    [bool]IsComplete() {
        return -not (
            [string]::IsNullOrWhiteSpace($this.NamespaceName) -or
            [string]::IsNullOrWhiteSpace($this.CertificateAuthorityName) -or
            [string]::IsNullOrWhiteSpace($this.CertificatePolicyName)
        )
    }

    [hashtable]ToHashtable() {
        return [ordered]@{
            NamespaceName = $this.NamespaceName
            CertificateAuthorityName = $this.CertificateAuthorityName
            CertificatePolicyName = $this.CertificatePolicyName
        }
    }

    static [AdrPolicyReference]FromHashtable([hashtable]$Hashtable) {
        if ($null -eq $Hashtable) { return [AdrPolicyReference]::new() }
        return [AdrPolicyReference]::new($Hashtable.NamespaceName, $Hashtable.CertificateAuthorityName, $Hashtable.CertificatePolicyName)
    }
}


class DpsInfo {
    [string]$ResourceGroup = $null
    [string]$DeviceFqdn = $null
    [string]$ServiceFqdn = $null
    [string]$ConnectionString = $null
    [string]$IdScope = $null
    [X509CertificateInfo[]]$RootCaCertificates = @()
    [DpsEnrollmentsSet]$Enrollments = [DpsEnrollmentsSet]::new()
    [string[]]$LinkedIotHubs = @()
    # Always present, never null: an environment without certificate management simply carries an
    # incomplete reference. Callers gate on IsComplete(), and the generated test configuration reads
    # the three names directly.
    [AdrPolicyReference]$AdrPolicy = [AdrPolicyReference]::new()

    DpsInfo() { }

    [string]GetName() {
        return $this.ServiceFqdn.split(".")[0]
    }

    [X509CertificateInfo]AddRootCaCertificate() {
        $DpsRootCertificate = Add-DpsCertificate -ResourceGroup $this.ResourceGroup -DpsName $this.GetName()
        $this.RootCaCertificates += $DpsRootCertificate
        return $DpsRootCertificate
    }

    [DpsX509EnrollmentGroupInfo]AddX509GroupEnrollment([string]$EnrollmentId) {
        return $this.AddX509GroupEnrollment($EnrollmentId, $null, $null, $null, $null, $null, $true)
    }

    [DpsX509EnrollmentGroupInfo]AddX509GroupEnrollment(
        [string]$EnrollmentId,
        [string]$IotHubFqdn,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$IssuerCertificate,
        [System.Security.Cryptography.RSA]$IssuerPrivateKey,
        [AdrPolicyReference]$AdrPolicyReference,
        [timespan]$CertificateExpiration,
        [bool]$UseAdrPolicy
    ) {
        if ([string]::IsNullOrWhiteSpace($IotHubFqdn)) {
            if ($this.LinkedIotHubs.Count -gt 0) {
                $IotHubFqdn = $this.LinkedIotHubs[0]
            } else {
                throw "Cannot create DPS X509 enrollment group without IoT Hub FQDN (no linked IoT Hubs)"
            }
        }

        if ($null -eq $IssuerCertificate -and $null -eq $IssuerPrivateKey) {
            if ($this.RootCaCertificates.Count -eq 0) {
                $this.AddRootCaCertificate() | Out-Null
            }

            $IssuerCertificate = $this.RootCaCertificates[0].ToNativeX509Certificate2()
            $IssuerPrivateKey = $this.RootCaCertificates[0].PrivateKey.ToNativeRsaKey()
        } elseif ($null -in ($IssuerCertificate, $IssuerPrivateKey)) {
            throw "Both IssuerCertificate and IssuerPrivateKey must be provided together"
        }

        if ($null -eq $AdrPolicyReference -and $UseAdrPolicy) {
            $AdrPolicyReference = $this.AdrPolicy
        }

        if ($null -eq $CertificateExpiration) {
            $DefaultCertificateExpiration = [TimeSpan]::FromDays(365)

            $CertificateExpiration = $DefaultCertificateExpiration
        }

        $GroupX509Enrollment = Add-DpsX509EnrollmentGroup -ResourceGroup $this.ResourceGroup -DpsName $this.GetName() -EnrollmentId $EnrollmentId -IssuerCertificate $IssuerCertificate -IssuerPrivateKey $IssuerPrivateKey -IotHubFqdn $IotHubFqdn -AdrPolicy $AdrPolicyReference -CertificateExpiration $CertificateExpiration
        $this.Enrollments.GroupX509 += [DpsX509EnrollmentGroupInfo]::new($GroupX509Enrollment.Id, $GroupX509Enrollment.PrimaryCertificate)
        return $GroupX509Enrollment
     }

     [hashtable]ToHashtable() {
        return [ordered]@{
            ResourceGroup = $this.ResourceGroup
            DeviceFqdn = $this.DeviceFqdn
            ServiceFqdn = $this.ServiceFqdn
            ConnectionString = $this.ConnectionString
            IdScope = $this.IdScope
            RootCaCertificates = Convert-CollectionToHashtable -Collection $this.RootCaCertificates
            Enrollments =  ConvertTo-Hashtable -Object $this.Enrollments
            LinkedIotHubs = $this.LinkedIotHubs
            AdrPolicy = $this.AdrPolicy.ToHashtable()
        }
     }

    static [DpsInfo]FromHashtable([hashtable]$Hashtable) {
        $DpsInfo = [DpsInfo]::new()
        $DpsInfo.ResourceGroup = $Hashtable.ResourceGroup
        $DpsInfo.DeviceFqdn = $Hashtable.DeviceFqdn
        $DpsInfo.ServiceFqdn = $Hashtable.ServiceFqdn
        $DpsInfo.ConnectionString = $Hashtable.ConnectionString
        $DpsInfo.IdScope = $Hashtable.IdScope
        if ($null -ne $Hashtable.RootCaCertificates) { $DpsInfo.RootCaCertificates = @($Hashtable.RootCaCertificates | ?{ $null -ne $_ } | %{ [X509CertificateInfo]::FromHashtable($_) }) }
        $DpsInfo.Enrollments = [DpsEnrollmentsSet]::FromHashtable($Hashtable.Enrollments)
        $DpsInfo.LinkedIotHubs = $Hashtable.LinkedIotHubs
        $DpsInfo.AdrPolicy = [AdrPolicyReference]::FromHashtable($Hashtable.AdrPolicy)
        return $DpsInfo
    }
}

class EventHubInfo {
    [string]$ConnectionString = $null
    [string]$CompatibleName = $null
    [int]$PartitionCount = 0
    [array]$ConsumerGroups = @()

    EventHubInfo() { }

    [hashtable]ToHashtable() {
        return [ordered]@{
            ConnectionString = $this.ConnectionString
            CompatibleName = $this.CompatibleName
            PartitionCount = $this.PartitionCount
            ConsumerGroups = $this.ConsumerGroups
        }
    }

    static [EventHubInfo]FromHashtable([hashtable]$Hashtable) {
        $EventHubInfo = [EventHubInfo]::new()
        $EventHubInfo.ConnectionString = $Hashtable.ConnectionString
        $EventHubInfo.CompatibleName = $Hashtable.CompatibleName
        $EventHubInfo.PartitionCount = $Hashtable.PartitionCount
        $EventHubInfo.ConsumerGroups = $Hashtable.ConsumerGroups
        return $EventHubInfo
    }
}

class IotHubDeviceSet {
    [IotHubSymmetricKeyIdentityInfo[]]$SymmetricKey = @()
    [IotHubX509IdentityInfo[]]$X509Thumbprint = @()
    # $X509CA = @()

    IotHubDeviceSet() { }

    [hashtable]ToHashtable() {
        return [ordered]@{
            SymmetricKey = Convert-CollectionToHashtable -Collection $this.SymmetricKey
            X509Thumbprint = Convert-CollectionToHashtable -Collection $this.X509Thumbprint
        }
    }

    static [IotHubDeviceSet]FromHashtable([hashtable]$Hashtable) {
        $IotHubDeviceSet = [IotHubDeviceSet]::new()
        if ($null -ne $Hashtable.SymmetricKey) { $IotHubDeviceSet.SymmetricKey = @($Hashtable.SymmetricKey | ?{ $null -ne $_ } | %{ [IotHubSymmetricKeyIdentityInfo]::FromHashtable($_) }) }
        if ($null -ne $Hashtable.X509Thumbprint) { $IotHubDeviceSet.X509Thumbprint = @($Hashtable.X509Thumbprint | ?{ $null -ne $_ } | %{ [IotHubX509IdentityInfo]::FromHashtable($_) }) }
        return $IotHubDeviceSet
    }
}

class IotHubInfo {
    [string]$ConnectionString = $null
    [EventHubInfo]$EventHub = [EventHubInfo]::new()
    [IotHubDeviceSet]$Devices = [IotHubDeviceSet]::new()

    IotHubInfo() { }

    [hashtable]ToHashtable() {
        return [ordered]@{
            ConnectionString = $this.ConnectionString
            EventHub = ConvertTo-Hashtable -Object $this.EventHub
            Devices = ConvertTo-Hashtable -Object $this.Devices
        }
    }

    static [IotHubInfo]FromHashtable([hashtable]$Hashtable) {
        $IotHubInfo = [IotHubInfo]::new()
        $IotHubInfo.ConnectionString = $Hashtable.ConnectionString
        $IotHubInfo.EventHub = [EventHubInfo]::FromHashtable($Hashtable.EventHub)
        $IotHubInfo.Devices = [IotHubDeviceSet]::FromHashtable($Hashtable.Devices)
        return $IotHubInfo
    }
}

class ContainerRegistryInfo {
    [string]$Name = $null
    [string]$LoginServer = $null
    [bool]$AdminUserEnabled = $false
    [string]$Username = $null
    [string]$Password = $null

    ContainerRegistryInfo(
        [string]$Name,
        [string]$LoginServer,
        [bool]$AdminUserEnabled,
        [string]$Username,
        [string]$Password
     ) {
        $this.Name = $Name
        $this.LoginServer = $LoginServer
        $this.AdminUserEnabled = $AdminUserEnabled
        $this.Username = $Username
        $this.Password = $Password
     }

     ContainerRegistryInfo() { }
}

class TestEnvironmentInfo {
    [string]$AzureResourceGroup = $null

    [IotHubInfo]$IotHub = [IotHubInfo]::new()

    [DpsInfo]$Dps = [DpsInfo]::new()

    [ContainerRegistryInfo[]]$ContainerRegistry = @()

    # Always present, never null: an environment without certificate management simply carries an
    # incomplete reference. Callers gate on IsComplete(), and the generated test configuration reads
    # the three names directly.
    [AdrPolicyReference]$AdrPolicy = [AdrPolicyReference]::new()

    [hashtable]ToHashtable() {
        return [ordered]@{
            AzureResourceGroup = $this.AzureResourceGroup
            IotHub = ConvertTo-Hashtable -Object $this.IotHub
            Dps = ConvertTo-Hashtable -Object $this.Dps
            # TODO: add container registry
            AdrPolicy = $this.AdrPolicy.ToHashtable()
        }
    }

    static [TestEnvironmentInfo]FromHashtable([hashtable]$Hashtable) {
        $TestEnvironmentInfo = [TestEnvironmentInfo]::new()
        $TestEnvironmentInfo.AzureResourceGroup = $Hashtable.AzureResourceGroup
        $TestEnvironmentInfo.AdrPolicy = [AdrPolicyReference]::FromHashtable($Hashtable.AdrPolicy)
        $TestEnvironmentInfo.IotHub = [IotHubInfo]::FromHashtable($Hashtable.IotHub)
        $TestEnvironmentInfo.Dps = [DpsInfo]::FromHashtable($Hashtable.Dps)
        # TODO: add container registry
        return $TestEnvironmentInfo
    }


    [string]ToJson() {
        return ($this.ToHashtable() | ConvertTo-Json -Depth 20)
    }

    static [TestEnvironmentInfo]FromJson([string]$Json) {
        return [TestEnvironmentInfo]::FromHashtable($(ConvertFrom-PSObject $($Json | ConvertFrom-Json)))
    }
}


# <[Azure Device Registry (ADR) Helper Functions]>

# ADR resources are created through ARM directly: the azure-iot CLI extension only ever exposed the
# public-preview object model (a namespace credential holding policies, selected by name) and has no
# command for the certificate-authority model that replaced it.
#
# Overridable from the environment so a cloud or region where one of these versions is not registered
# can be unblocked without a code change.
$script:AdrApiVersion = if ($env:ADR_API_VERSION) { $env:ADR_API_VERSION } else { "2026-11-02-preview" }
$script:DpsControlPlaneApiVersion = if ($env:DPS_CONTROL_PLANE_API_VERSION) { $env:DPS_CONTROL_PLANE_API_VERSION } else { "2026-03-01-preview" }
$script:DpsEnrollmentApiVersion = if ($env:DPS_ENROLLMENT_API_VERSION) { $env:DPS_ENROLLMENT_API_VERSION } else { "2026-11-01" }

# Azure Device Registry Contributor: namespaces/read, namespaces/devices/*.
$script:AdrContributorRoleId = "a5c3590a-3a1a-4cd4-9648-ea0a32b15137"
# IoT Hub Data Contributor: the namespace identity writes device identities into the linked hub.
$script:IotHubDataContributorRoleId = "4fc6c259-987e-4a07-842e-c321cc9d413f"
# Contributor.
$script:ContributorRoleId = "b24988ac-6180-42a0-ab88-20f7382dd24c"

# The namespace link saga runs as the namespace's managed identity, whose grants are eventually
# consistent. Until they replicate, linking fails with one of these -- either outright, or by
# settling an endpoint to Failed after the fact. Both are recovered by re-submitting the same
# namespace, whose identity keeps replicating; everything else fails immediately.
$script:AdrRolePropagationPattern = 'AdrMiNotAuthorized|LinkableResourceNotReady|AuthorizationFailed|LinkInitiateFailed|NamespaceMiTokenAcquisitionFailed|OutboundIdentityUnavailable'
$script:AdrLinkMaxAttempts = 5

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
    } | Out-Null

    Wait-AzProvisioningState -Url $Url -Step "ADR namespace ($NamespaceName)"

    # Re-read rather than use the PUT response: the principalId is assigned asynchronously and can
    # still be absent from the body the create returned.
    return Invoke-AzRest -Url $Url
}

function Connect-AdrNamespace {
    <#
    .SYNOPSIS
    Links an IoT Hub and a DPS to an ADR namespace, and waits for the link to complete.

    .DESCRIPTION
    Replaces the public-preview wiring, where the hub and DPS were pointed at the namespace with
    '--ns-resource-id'/'--ns-identity-id' at creation time. The relationship is now expressed on the
    NAMESPACE, as endpoints: the hub is a messaging endpoint, the DPS a provisioning one. The two
    carry different resource types, and only the hub endpoint carries provisioning availability.

    The call returns immediately with the endpoints at linkingState=InProgress; ADR completes the
    link asynchronously. The saga runs as the namespace identity, so a link attempted before that
    identity's grants have replicated fails on a role-propagation error -- either outright, or by
    settling an endpoint to Failed once the saga runs. The failed endpoints are re-PUTtable, so the
    whole link is re-submitted against the same namespace, whose identity keeps replicating. A
    failure for any other reason is final and is raised on the spot.

    Linking can also leave the namespace at provisioningState=Failed with every endpoint Succeeded.
    That is healed here, because otherwise device registration later fails with errorCode 403000.
    #>
    param(
        [string]$NamespaceId,
        [string]$Location,
        [string]$IotHubId,
        [string]$DpsId
    )

    $Url = "https://management.azure.com$($NamespaceId)?api-version=$($script:AdrApiVersion)"
    $LinkBody = @{
        location = $Location
        identity = @{ type = "SystemAssigned" }
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
        Invoke-WithRetry -Step "Link IoT Hub and DPS to ADR namespace" `
            -RetryOnPattern $script:AdrRolePropagationPattern -MaxAttempts 3 -Command {
            Invoke-AzRest -Method PUT -Url $Url -Body $LinkBody
        } | Out-Null

        # Endpoint linkingState is the source of truth: the namespace itself can read Succeeded while
        # an endpoint is still InProgress, and a failed endpoint is where the reason is recorded.
        $Deadline = (Get-Date).AddSeconds(900)
        while ($true) {
            # As in Wait-AzProvisioningState, a failed read during a poll that runs for minutes is
            # transient and says nothing about the link, so it costs an attempt rather than the run.
            $Namespace = Invoke-AzRest -Url $Url -AllowFailure
            $Endpoints = if ($null -ne $Namespace) {
                @($Namespace.properties.messaging.endpoints.PSObject.Properties) + `
                @($Namespace.properties.provisioning.endpoints.PSObject.Properties)
            } else { @() }
            $States = @($Endpoints | %{ $_.Value.linkingState })

            if ($States.Count -gt 0 -and @($States | ?{ $_ -notin @("Succeeded", "Failed") }).Count -eq 0) {
                break
            }

            if ((Get-Date) -ge $Deadline) {
                throw "ADR namespace link did not complete within 900 seconds (endpoint states: $($States -join ', '))."
            }

            Write-Host "Waiting for ADR namespace link (endpoint states: $($States -join ', '))."
            Start-Sleep -Seconds 15
        }

        $Failed = @($Endpoints | ?{ $_.Value.linkingState -eq "Failed" })
        if ($Failed.Count -eq 0) {
            break
        }

        $FailedCode = $Failed[0].Value.linkingError.code
        if ($FailedCode -notmatch $script:AdrRolePropagationPattern -or $Attempt -eq $script:AdrLinkMaxAttempts) {
            throw "ADR namespace link failed for endpoint '$($Failed[0].Name)': $FailedCode."
        }

        Write-Host "Link endpoint '$($Failed[0].Name)' failed with $FailedCode while the namespace role assignments replicate; re-submitting."
        Start-Sleep -Seconds 30
    }

    # Heal a namespace left Failed by an otherwise successful link. A tags-only update re-runs
    # namespace reconciliation; re-sending the endpoints instead is rejected as immutable. The state
    # can read Failed for a while after the update is accepted, so it is polled rather than judged
    # on first read.
    if ($Namespace.properties.provisioningState -eq "Failed") {
        Write-Host "Namespace left at provisioningState=Failed after linking; reconciling."
        # Guarded because the namespace is created without tags: piping a null property into
        # ForEach-Object still runs the body once, with a null key.
        $Tags = @{}
        if ($null -ne $Namespace.tags) { $Namespace.tags.PSObject.Properties | %{ $Tags[$_.Name] = $_.Value } }
        $Tags["AdrReconcileUtc"] = (Get-Date).ToUniversalTime().ToString("o")
        Invoke-AzRest -Method PATCH -Url $Url -Body @{ tags = $Tags } | Out-Null

        Wait-AzProvisioningState -Url $Url -Step "ADR namespace reconcile" -TimeoutSeconds 300
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
        [string]$DpsId
    )

    $Url = "https://management.azure.com$($DpsId)?api-version=$($script:DpsControlPlaneApiVersion)"

    Write-Host "Pushing the linked ADR namespace into the DPS data plane (tags-only update)."
    try {
        # Guarded because the DPS is created without tags: piping a null property into ForEach-Object
        # still runs the body once, with a null key, which would fail the sync before it is attempted.
        $Dps = Invoke-AzRest -Url $Url
        $Tags = @{}
        if ($null -ne $Dps.tags) { $Dps.tags.PSObject.Properties | %{ $Tags[$_.Name] = $_.Value } }
        $Tags["AdrDataplaneSyncUtc"] = (Get-Date).ToUniversalTime().ToString("o")

        Invoke-AzRest -Method PATCH -Url $Url -Body @{ tags = $Tags } | Out-Null
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

    return "SharedAccessSignature sr=$([uri]::EscapeDataString($ServiceHost))&sig=$([uri]::EscapeDataString($Signature))&se=$Expiry&skn=$($Parts['SharedAccessKeyName'])"
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
    $Url = "https://$ServiceHost/$Collection/$($EnrollmentId)?api-version=$($script:DpsEnrollmentApiVersion)"
    $Headers = @(
        "Authorization=$(New-DpsServiceSasToken -ConnectionString $ConnectionString)",
        "Content-Type=application/json"
    )

    return Invoke-WithRetry -Step "Create DPS enrollment ($EnrollmentId)" `
        -RetryOnPattern '403000|400004' -MaxAttempts 8 -InitialDelaySeconds 15 -Command {
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

    $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
        registrationId = $EnrollmentId
        attestation = @{ type = "symmetricKey" }
        provisioningStatus = "enabled"
    }

    $EnrollmentInfo = Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollments" -EnrollmentId $EnrollmentId -Body $Body

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

    # An individual x509 enrollment pins the device's own certificate, so the certificate travels in
    # the request body rather than as a file path an 'az' command reads.
    $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
        registrationId = $EnrollmentId
        attestation = @{
            type = "x509"
            x509 = @{ clientCertificates = @{ primary = @{ certificate = [Convert]::ToBase64String($DpsDeviceCertificate.RawData) } } }
        }
        provisioningStatus = "enabled"
    }

    Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollments" -EnrollmentId $EnrollmentId -Body $Body | Out-Null

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

    $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
        enrollmentGroupId = $EnrollmentId
        attestation = @{ type = "symmetricKey" }
        provisioningStatus = "enabled"
    }

    $EnrollmentInfo = Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollmentGroups" -EnrollmentId $EnrollmentId -Body $Body

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

    return [DpsX509EnrollmentGroupInfo]::new($EnrollmentId, $ICA)
}

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


# <[Azure IoT Test Environment Public Functions]>

function New-AzIotTestEnvironment {
    <#
    .SYNOPSIS
    Creates a new set of Azure Resources for testing Azure IoT scenarios, including an IoT Hub and optionally a Device Provisioning Service, with different types of enrollments and devices.

    .DESCRIPTION
    Creates a new set of Azure Resources for testing Azure IoT scenarios, including an IoT Hub and optionally a Device Provisioning Service, with different types of enrollments and devices.

    .PARAMETER AzureLocation
    Specifies the Azure location for the resources. Default is "centraluseuap".
    .PARAMETER AzureSubscriptionId
    Specifies the Azure subscription ID. If not provided, the current Azure CLI session default subscription will be used.
    .PARAMETER ResourceGroup
    Specifies the name of the resource group. If not provided, a new resource group will be created.
    .PARAMETER ResourceGroupTags
    Specify a hashtable with the key/value pairs to use as tags for Azure Resource Group creation.
    See `az group create --tags` for more details.
    .PARAMETER DpsName
    Specifies the name of the Device Provisioning Service. If not provided, a new DPS will be created.
    .PARAMETER IotHubName
    Specifies the name of the IoT Hub. If not provided, a new IoT Hub will be created.
    .PARAMETER IotHubDomainName
    Specifies the domain name of the IoT Hub. Default is "azure-devices.net".
    .PARAMETER StorageAccountName
    Specifies the name of the Storage Account. If not provided, a new Storage Account will be created.
    .PARAMETER KeyVaultName
    Specifies the name of the Azure Key Vault to create and add the IoT Hub and DPS certificates to. If not provided, a random name will be generated.
    .PARAMETER DpsSymmKeyIndividualEnrollments
    Specifies the number of symmetric key individual enrollments to create in DPS. Default is 0.
    .PARAMETER DpsX509IndividualEnrollments
    Specifies the number of x509 individual enrollments to create in DPS. Default is 0.
    .PARAMETER DpsSymmKeyGroupEnrollmentDevices
    Specifies the number of devices to create under a symmetric key enrollment group in DPS. Default is 0.
    .PARAMETER DpsX509GroupEnrollmentDevices
    Specifies the number of devices to create under an x509 enrollment group in DPS. Default is 1.
    .PARAMETER IotHubSymmKeyDevices
    Specifies the number of symmetric key devices to create in IoT Hub. Default is 1.
    .PARAMETER IotHubX509ThumbprintDevices
    Specifies the number of x509 thumbprint devices to create in IoT Hub. Default is 1.
    .PARAMETER IotHubX509CADevices
    Specifies the number of x509 CA devices to create in IoT Hub. Default is 0.
    .PARAMETER EnableFileUpload
    Specifies whether to enable file upload in IoT Hub. Default is false.
    .PARAMETER NoDps
    Specifies whether to skip creating a Device Provisioning Service. Default is false.
    .PARAMETER EnableCertificateManagement
    Specifies whether to enable certificate management for IoT Hub and DPS using Azure Device Registry (ADR). Default is false.
    Creates an ADR namespace, links the IoT Hub and DPS to it, and creates the certificate authority chain devices are issued certificates from. Requires a DPS, so it cannot be combined with -NoDps.

    .OUTPUTS
    A custom object containing information about the created Azure resources and devices, including connection strings, certificate paths, and enrollment details.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotTestEnvironment

    This command creates a new Azure IoT test environment in the default location with 1 x509 group enrollment device in DPS and 1 symmetric key device and 1 x509 thumbprint device in IoT Hub, without enabling certificate management nor file upload on Azure IoT Hub.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotTestEnvironment -AzureLocation "eastus2" -DpsSymmKeyIndividualEnrollments 2 -DpsX509IndividualEnrollments 1 -DpsSymmKeyGroupEnrollmentDevices 2 -DpsX509GroupEnrollmentDevices 2 -IotHubSymmKeyDevices 2 -IotHubX509ThumbprintDevices 1 -IotHubX509CADevices 1
    
    This command creates a new Azure IoT test environment in the "eastus2" location with 2 symmetric key individual enrollments, 1 x509 individual enrollment, 2 devices under a symmetric key enrollment group, 2 devices under an x509 enrollment group in DPS, and 2 symmetric key devices, 1 x509 thumbprint device, and 1 x509 CA device in IoT Hub.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotTestEnvironment -EnableCertificateManagement
    
    This command creates a new Azure IoT test environment with an IoT Hub and Device Provisioning Service that has certificate management enabled using Azure Device Registration (ADR).
    #>
    param(
        [string]$AzureLocation = "centraluseuap", # Other locations (e.g.): eastus2euap, westus2, ...
        [string]$AzureSubscriptionId = $null,
        [string]$ResourceGroup = $(New-AzureResourceGroupName),
        [Hashtable]$ResourceGroupTags = $null,
        [string]$DpsName       = "dps-$(New-GuidString -NoDashes)",
        [string]$IotHubName    = "iothub-$(New-GuidString -NoDashes)",
        [string]$IotHubDomainName = "azure-devices.net",
        [string]$StorageAccountName = "stoacc$(New-GuidString -NoDashes -MaxLength  18)", # Max size of Storage Account name is 24 characters.
        [string]$KeyVaultName = "kv-$(New-GuidString -NoDashes -MaxLength 21)", # Max size of Key Vault name is 24 characters.
        [int]$DpsSymmKeyIndividualEnrollments = 0,
        [int]$DpsX509IndividualEnrollments = 0,
        [int]$DpsSymmKeyGroupEnrollmentDevices = 0,
        [int]$DpsX509GroupEnrollmentDevices = 0,
        [int]$IotHubSymmKeyDevices = 0,
        [int]$IotHubX509ThumbprintDevices = 0,
        [int]$IotHubX509CADevices = 0,
        [switch]$EnableFileUpload,
        [switch]$NoDps,
        [switch]$EnableCertificateManagement,
        [switch]$AddContainerRegistry
    )

    $IotHubFqdn = "$($IotHubName).$($IotHubDomainName)"

    # Login to Azure if not already
    $null = & az account show 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Not logged in to Azure. Running 'az login'..."
        & az login --use-device-code
        if ($LASTEXITCODE -ne 0) {
            throw "Azure login failed."
        }
    }
    else {
        Write-Host "Already logged in to Azure."
    }

    $AzureAccount = az account show | ConvertFrom-Json
    $IsAzureAccountServicePrincipal = $AzureAccount.user.type -eq "servicePrincipal"

    # Subscription id...
    if ([string]::IsNullOrWhiteSpace($AzureSubscriptionId)) {
        Stop-OnError -Step "Get Azure account information"
        $AzureSubscriptionId = $AzureAccount.id
    } else {
        $discard = az account set --subscription "$AzureSubscriptionId" --only-show-errors
        Stop-OnError -Step "Set Azure subscription"
    }

    # Required for the IoT Hub and DPS command groups. ADR is reached through ARM directly.
    Install-AzureIotCliExtension

    # Add default Azure resource group tags 
    if ($ResourceGroupTags -eq $null) {
        $ResourceGroupTags = @{}
    }

    $AzureDevOpsRunUrl = Get-AzureDevOpsRunUrl
    if ($null -ne $AzureDevOpsRunUrl) {
        $ResourceGroupTags.Add("AzDevOpsRunUrl", $AzureDevOpsRunUrl)
    }

    # Create resource group (if does not exist).
    $ResourceGroupExists = az group exists --name $ResourceGroup -o tsv
    if ($ResourceGroupExists -eq 'true') {
        if (-not $ResourceGroupTags.ContainsKey("UpdatedBy")) {
            $ResourceGroupTags.Add("UpdatedBy", $AzureAccount.user.name)
        }

        if (-not $ResourceGroupTags.ContainsKey("UpdatedOn")) {
            $ResourceGroupTags.Add("UpdatedOn", (Get-Date).ToString("o"))
        }

        $ResourceGroupTagsString = Join-Hashtable -Hashtable $ResourceGroupTags

        Write-Host "Updating Azure resource group ($ResourceGroup; $ResourceGroupTagsString)"

        $AzureResourceGroup = az group show --name "$ResourceGroup" | ConvertFrom-Json

        Set-ResourceGroupTags -ResourceGroupId $AzureResourceGroup.id -Tags $ResourceGroupTags
        Stop-OnError -Step "Update Azure resource group tags"
    } else {
        if (-not $ResourceGroupTags.ContainsKey("CreatedBy")) {
            $ResourceGroupTags.Add("CreatedBy", $AzureAccount.user.name)
        }

        if (-not $ResourceGroupTags.ContainsKey("CreatedOn")) {
            $ResourceGroupTags.Add("CreatedOn", (Get-Date).ToString("o"))
        }

        $ResourceGroupTagsString = Join-Hashtable -Hashtable $ResourceGroupTags

        Write-Host "Creating Azure resource group ($ResourceGroup; $ResourceGroupTagsString)"

        # Created and tagged in one call, so the group is never observable in an untagged
        # state that the leftover-resource cleanup would have to skip forever.
        $AzureResourceGroup = New-AzureResourceGroup -SubscriptionId $AzureSubscriptionId -ResourceGroup $ResourceGroup -Location $AzureLocation -Tags $ResourceGroupTags

        Stop-OnError -Step "Create Azure resource group"
    }

    $TestEnvInfo = [TestEnvironmentInfo]::new()

    # TODO: create Storage Account (required for IoT Hub file upload, if enabled) and add to $TestEnvInfo
    # Write-Host "Creating Azure Key Vault ($KeyVaultName)"
    # $AzureKeyVault = az keyvault create --name "$KeyVaultName" --resource-group "$ResourceGroup" --location "$AzureLocation" 2>$null | ConvertFrom-Json
    # Stop-OnError -Step "Create Azure Key Vault"

    # Certificate management is wired up in a different order from everything else here. The hub and
    # the DPS are created plain, and the ADR namespace is then LINKED to them afterwards -- the
    # relationship used to be established at creation time, by pointing both resources at a namespace
    # and a user-assigned identity, and that is no longer how ADR models it. Each resource now
    # authenticates as its own system-assigned identity, so the shared identity is gone too.
    Write-Host "Creating Azure IoT Hub ($IotHubName)."
    $AzureIoTHub = az iot hub create --name "$IotHubName" --resource-group "$ResourceGroup" --location "$AzureLocation" --mintls "1.2" --mi-system-assigned | ConvertFrom-Json
    Stop-OnError -Step "Create Azure IoT Hub"

    if ($NoDps -eq $false) {
        # Created through ARM rather than 'az iot dps create' so it comes up WITH a system-assigned
        # identity, which is what authenticates it to the ADR namespace. The identity cannot be added
        # afterwards -- DPS rejects a managed-identity PATCH with IH400158 -- and the CLI accepts
        # identity flags only in preview builds of the azure-iot extension, so neither route works.
        Write-Host "Creating Azure Device Provisioning Service ($DpsName)."
        $DpsUrl = "https://management.azure.com/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Devices/provisioningServices/$($DpsName)?api-version=$($script:DpsControlPlaneApiVersion)"
        Invoke-AzRest -Method PUT -Url $DpsUrl -Body @{
            location = $AzureLocation
            sku = @{ name = "S1"; capacity = 1 }
            identity = @{ type = "SystemAssigned" }
            properties = @{}
        } | Out-Null
        Wait-AzProvisioningState -Url $DpsUrl -Step "Device Provisioning Service ($DpsName)" -TimeoutSeconds 1200
        # Re-read: idScope and the identity's principalId are populated as it provisions.
        $AzureDps = Invoke-AzRest -Url $DpsUrl
    }

    if ($EnableCertificateManagement -eq $true) {
        if ($NoDps -eq $true) {
            throw "Certificate management requires a Device Provisioning Service; -NoDps and -EnableCertificateManagement are mutually exclusive."
        }

        $AzureAdrNamespaceName = "azure-adr-ns"
        $AzureAdrPolicyName = "azure-adr-policy"
        $AzureAdrCertificateAuthorityName = "default"

        $AzureAdrNamespace = New-AdrNamespace -SubscriptionId $AzureSubscriptionId -ResourceGroup $ResourceGroup -NamespaceName $AzureAdrNamespaceName -Location $AzureLocation

        # Grants in both directions: the hub and DPS identities read the namespace, and the namespace
        # identity writes device identities into the hub. The 'Azure Device Registry Onboarding' role
        # the previous model needed is not used any more -- issuing certificates is authorized
        # through the namespace link, not through a role on a shared identity.
        Write-Host "Assigning roles between the ADR namespace, the IoT Hub and the DPS"
        @(
            @{ Assignee = $AzureIoTHub.identity.principalId;            Role = $script:AdrContributorRoleId;         Scope = $AzureAdrNamespace.id },
            @{ Assignee = $AzureDps.identity.principalId;               Role = $script:AdrContributorRoleId;         Scope = $AzureAdrNamespace.id },
            @{ Assignee = $AzureAdrNamespace.identity.principalId;      Role = $script:ContributorRoleId;            Scope = $AzureIoTHub.id },
            @{ Assignee = $AzureAdrNamespace.identity.principalId;      Role = $script:IotHubDataContributorRoleId;  Scope = $AzureIoTHub.id }
        ) | %{
            az role assignment create --assignee-object-id $_.Assignee --assignee-principal-type ServicePrincipal --role $_.Role --scope $_.Scope --only-show-errors | Out-Null
            Stop-OnError -Step "Assign role $($_.Role) on $($_.Scope)"
        }

        Wait-AzRoleAssignment `
            -PrincipalId "$($AzureAdrNamespace.identity.principalId)" `
            -Scope "$($AzureIoTHub.id)" `
            -RoleDefinitionIds @($script:ContributorRoleId, $script:IotHubDataContributorRoleId)

        Connect-AdrNamespace -NamespaceId $AzureAdrNamespace.id -Location $AzureLocation -IotHubId $AzureIoTHub.id -DpsId $AzureDps.id

        # After the link, so that ADR has a hub to sync the issuing CA certificate to.
        New-AdrCertificateAuthority -NamespaceId $AzureAdrNamespace.id -Location $AzureLocation `
            -CertificateAuthorityName $AzureAdrCertificateAuthorityName -PolicyName $AzureAdrPolicyName | Out-Null

        Sync-DpsAdrConfiguration -DpsId $AzureDps.id

        $AzureAdrPolicy = [AdrPolicyReference]::new($AzureAdrNamespaceName, $AzureAdrCertificateAuthorityName, $AzureAdrPolicyName)
    } else {
        $AzureAdrPolicy = [AdrPolicyReference]::new() # Incomplete: no policy is referenced below.
    }

    if ($NoDps -eq $false) {
        # A DPS linked to an ADR namespace has ADR choosing its provisioning targets, and its own
        # linked-hub list is read-only from then on -- adding to it fails with IH409313.
        if ($EnableCertificateManagement -eq $false) {
            Write-Host "Linking Azure IoT Hub ($IotHubName) to Azure Device Provisioning service ($DpsName)"
            az iot dps linked-hub create --dps-name "$DpsName" --resource-group "$ResourceGroup" --hub-name "$IotHubName" | Out-Null
            Stop-OnError -Step "Link Azure IoT Hub to Azure Device Provisioning service"
        }

        # Step was put here to optimize if blocks, since it's common down.
        Write-Host "Creating DPS Root Certificate"
        $DpsRootCertificate = Add-DpsCertificate -ResourceGroup $ResourceGroup -DpsName $DpsName
    }

    # Create IoT Hub Devices
    for ($i = 0; $i -lt $IotHubSymmKeyDevices; $i++) {
        $IotHubDeviceId = "sk-$(New-GuidString -NoDashes)"

        Write-Host "Creating Azure IoT Hub symmetric-key device ($IotHubDeviceId)"
        $IotHubDeviceInfo = az iot hub device-identity create --resource-group $ResourceGroup --hub-name $IotHubName --device-id $IotHubDeviceId | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub symmetric-key device ($IotHubDeviceId)"
        $PrimaryConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $IotHubDeviceId --kt primary | ConvertFrom-Json
        Stop-OnError -Step "Get Azure IoT Hub device primary connection-string ($IotHubDeviceId)"
        $SecondaryConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $IotHubDeviceId --kt secondary | ConvertFrom-Json
        Stop-OnError -Step "Get Azure IoT Hub device secondary connection-string ($IotHubDeviceId)"

        $DeviceIdentity = [IotHubSymmetricKeyIdentityInfo]::new(
            $IotHubDeviceId,
            $IotHubDeviceInfo.authentication.symmetricKey.primaryKey,
            $IotHubDeviceInfo.authentication.symmetricKey.secondaryKey,
            $PrimaryConnectionString.connectionString,
            $SecondaryConnectionString.connectionString            
        )

        $TestEnvInfo.IotHub.Devices.SymmetricKey += $DeviceIdentity
    }

    for ($i = 0; $i -lt $IotHubX509ThumbprintDevices; $i++) {
        $IotHubDeviceId = "x509tp-$(New-GuidString -NoDashes)"
        $CertificateSubjectName = "C=US, ST=Washington, L=Redmond, O=Company, OU=Org, CN=www.company.com"

        $IotHubDevicePrivateKey = New-RsaPrivateKey
        $IotHubDevicePrimaryCertificate = New-Certificate -Subject $CertificateSubjectName -Key $IotHubDevicePrivateKey
        $IotHubDeviceSecondaryCertificate = New-Certificate -Subject $CertificateSubjectName -Key $IotHubDevicePrivateKey

        Write-Host "Creating Azure IoT Hub x509 thumbprint device ($IotHubDeviceId)"
        $IotHubDeviceInfo = az iot hub device-identity create --resource-group $ResourceGroup --hub-name $IotHubName --device-id $IotHubDeviceId `
            --am x509_thumbprint --ptp $IotHubDevicePrimaryCertificate.Thumbprint --stp $IotHubDeviceSecondaryCertificate.Thumbprint | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub x509 thumbprint device ($IotHubDeviceId)"

        $ConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $IotHubDeviceId | ConvertFrom-Json
        Stop-OnError -Step "Get Azure IoT Hub device connection-string ($IotHubDeviceId)"

        $DeviceIdentity = [IotHubX509IdentityInfo]::new(
            $IotHubDeviceId,
            $ConnectionString.connectionString,
            [X509CertificateInfo]::new($IotHubDevicePrivateKey, $IotHubDevicePrimaryCertificate),
            [X509CertificateInfo]::new($IotHubDevicePrivateKey, $IotHubDeviceSecondaryCertificate)
        )

        $TestEnvInfo.IotHub.Devices.X509Thumbprint += $DeviceIdentity
    }
    # TODO: implement this...
    # $IotHubX509CADevices = 0
    # IotHubX509CADevices = @()
    # $TestEnvInfo.IotHub.Devices.X509CA = @()

    $DpsSymmKeyEnrollmentIdPrefix = "test-enrollment-sk"
    $DpsX509EnrollmentIdPrefix = "test-enrollment-x509"

    # Create all enrollments 
    if ($NoDps -eq $false) {
        for ($i = 0; $i -lt $DpsSymmKeyIndividualEnrollments; $i++) {
            $EnrollmentId = "$DpsSymmKeyEnrollmentIdPrefix-$i"
            $EnrollmentInfo = Add-DpsSymmetricKeyIndividualEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicy $AzureAdrPolicy

            $TestEnvInfo.Dps.Enrollments.IndividualSymmetricKey += $EnrollmentInfo
        }

        for ($i = 0; $i -lt $DpsX509IndividualEnrollments; $i++) {
            $EnrollmentId = "$DpsX509EnrollmentIdPrefix-$i"
            $EnrollmentInfo = Add-DpsX509IndividualEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicy $AzureAdrPolicy

            $TestEnvInfo.Dps.Enrollments.IndividualX509 += $EnrollmentInfo
        }

        if ($DpsSymmKeyGroupEnrollmentDevices -gt 0) {
            $EnrollmentId = "$DpsSymmKeyEnrollmentIdPrefix-group"
            $SKEnrollmentGroupInfo = Add-DpsSymmetricKeyEnrollmentGroup -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicy $AzureAdrPolicy

            $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey += $SKEnrollmentGroupInfo

            for ($i = 0; $i -lt $DpsSymmKeyGroupEnrollmentDevices; $i++) {
                $SKEnrollmentGroupInfo.AddIdentity("group-prov-sk-$i") | Out-Null
            }
        }

        if ($DpsX509GroupEnrollmentDevices -gt 0) {
            $EnrollmentId = "$DpsX509EnrollmentIdPrefix-group"
            $X509EnrollmentGroupInfo = Add-DpsX509EnrollmentGroup -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicy $AzureAdrPolicy -IssuerCertificate $DpsRootCertificate.ToNativeX509Certificate2() -IssuerPrivateKey $DpsRootCertificate.PrivateKey.ToNativeRsaKey() -IotHubFqdn $IotHubFqdn

            $TestEnvInfo.Dps.Enrollments.GroupX509 += $X509EnrollmentGroupInfo

            for ($i = 0; $i -lt $DpsX509GroupEnrollmentDevices; $i++) {
                $X509EnrollmentGroupInfo.AddIdentity("group-prov-x509-$i", $DefaultCertificateExpiration) | Out-Null
            }
        }
    }

    # File Upload
    if ($EnableFileUpload -eq $true) {
        Write-Host "Creating Azure Storage account ($StorageAccountName)"
        az storage account create --name "$StorageAccountName" --resource-group "$ResourceGroup" --location "$AzureLocation" --sku Standard_LRS --kind StorageV2 | Out-Null
        Stop-OnError -Step "Creating Azure Storage account"

        $AzureStorageContainerName = "iothubuploads"

        Write-Host "Creating Azure Storage container ($AzureStorageContainerName on $StorageAccountName)"
        az storage container create --name $AzureStorageContainerName --account-name "$StorageAccountName" --only-show-errors | Out-Null
        Stop-OnError -Step "Creating Azure Storage container"

        Write-Host "Getting Azure Storage account connection string"
        $AzureStorageConnectionString=$(az storage account show-connection-string --name "$StorageAccountName" --resource-group "$ResourceGroup" --query connectionString -o tsv)
        Stop-OnError -Step "Getting Azure Storage account connection string"

        # File upload no longer varies with certificate management: '--ns-identity-id' belonged to the
        # model where the hub pointed at the namespace through a shared identity.
        Write-Host "Updating Azure IoT Hub file upload settings"
        az iot hub update --name "$IotHubName" --resource-group "$ResourceGroup" --fcs "$AzureStorageConnectionString" --fc $AzureStorageContainerName --fileupload-sas-ttl 1 | Out-Null
        Stop-OnError -Step "Updating Azure IoT Hub file upload settings"
    }

    if ($AddContainerRegistry) {
        $ContainerRegistryName = "cr$(New-GuidString -NoDashes -MaxLength 22)" # Max length for container registry is 24, and we need to add a prefix.
        Write-Host "Creating Azure Container Registry ($ContainerRegistryName)"
        $AzureContainerRegistry = az acr create --name "$ContainerRegistryName" --resource-group "$ResourceGroup" --location "$AzureLocation" --sku Basic --admin-enabled true | ConvertFrom-Json
        Stop-OnError -Step "Create Azure Container Registry"

        Write-Host "Getting Azure Container Registry credentials"
        $AzureContainerRegistrySecret = az acr credential show --name "$ContainerRegistryName" --resource-group "$ResourceGroup" | ConvertFrom-Json
        Stop-OnError -Step "Get Azure Container Registry credentials"

        $ContainerRegistryInfo = [ContainerRegistryInfo]::new(
            $AzureContainerRegistry.name,
            $AzureContainerRegistry.loginServer,
            $AzureContainerRegistry.adminUserEnabled,
            $AzureContainerRegistrySecret.username,
            $AzureContainerRegistrySecret.passwords[0].value
        )

        $TestEnvInfo.ContainerRegistry += $ContainerRegistryInfo
    }

    # Gathering Test Environment settings.
    $TestEnvInfo.AzureResourceGroup = $ResourceGroup
    $TestEnvInfo.Dps.ResourceGroup = $ResourceGroup
    $TestEnvInfo.AdrPolicy = $AzureAdrPolicy
    $TestEnvInfo.Dps.AdrPolicy = $AzureAdrPolicy

    Write-Host "Getting IoT Hub Connection String"
    $TestEnvInfo.IotHub.ConnectionString = $(az iot hub connection-string show -g $ResourceGroup -n $IotHubName --kt primary --pn iothubowner --query connectionString -o tsv)
    Stop-OnError -Step "Get IoT Hub Connection String"

    Write-Host "Getting IoT Hub's Event Hub Connection String"
    $TestEnvInfo.IotHub.EventHub.ConnectionString = $(az iot hub connection-string show -g $ResourceGroup -n $IotHubName --kt primary --pn iothubowner --eh --query connectionString -o tsv)
    Stop-OnError -Step "Get IoT Hub's Event Hub Connection String"

    $TestEnvInfo.IotHub.EventHub.CompatibleName = $AzureIoTHub.properties.eventHubEndpoints.events.path
    $TestEnvInfo.IotHub.EventHub.PartitionCount = $AzureIoTHub.properties.eventHubEndpoints.events.partitionCount

    Write-Host "Getting IoT Hub's Event Hub Consumer Groups"
    az iot hub consumer-group list --hub-name $IotHubName --resource-group $ResourceGroup | ConvertFrom-Json | %{ $TestEnvInfo.IotHub.EventHub.ConsumerGroups += $_.name }
    Stop-OnError -Step "Get IoT Hub's Event Hub Consumer Groups"

    if ($NoDps -eq $false) {
        $TestEnvInfo.Dps.DeviceFqdn = $AzureDps.properties.deviceProvisioningHostName
        $TestEnvInfo.Dps.ServiceFqdn = $AzureDps.properties.serviceOperationsHostName
        $TestEnvInfo.Dps.IdScope = $AzureDps.properties.idScope
        # Not read from the DPS: it is captured before the hub is attached, and a DPS linked to an
        # ADR namespace does not carry its provisioning targets in its own list at all.
        $TestEnvInfo.Dps.LinkedIotHubs += $IotHubFqdn

        Write-Host "Getting DPS Connection String"
        $TestEnvInfo.Dps.ConnectionString = $(az iot dps connection-string show -g $ResourceGroup -n $DpsName --kt primary --pn provisioningserviceowner --query connectionString -o tsv)
        Stop-OnError -Step "Get DPS Connection String"

        $TestEnvInfo.Dps.RootCaCertificates += $DpsRootCertificate
    }

    return $TestEnvInfo
}

function Get-AzIotTestEnvironment {
    <#
    .SYNOPSIS
    Creates a new set of Azure Resources for testing Azure IoT scenarios, including an IoT Hub and optionally a Device Provisioning Service, with different types of enrollments and devices.

    .DESCRIPTION
    Creates a new set of Azure Resources for testing Azure IoT scenarios, including an IoT Hub and optionally a Device Provisioning Service, with different types of enrollments and devices.

    .PARAMETER AzureSubscriptionId
    Specifies the Azure subscription ID. If not provided, the current Azure CLI session default subscription will be used.
    .PARAMETER ResourceGroup
    Specifies the name of the resource group. If not provided, a new resource group will be created.
    .PARAMETER DpsName
    Specifies the name of the Device Provisioning Service. If not provided, get the one instance in the resource group.
    .PARAMETER IotHubName
    Specifies the name of the IoT Hub. If not provided, get the IoT Hub linked to the DPS or with the specified name.

    .OUTPUTS
    A custom object containing information about the created Azure resources and devices, including connection strings, certificate paths, and enrollment details.

    .EXAMPLE
    PS> $TestEnvInfo = Get-AzIotTestEnvironment -ResourceGroup "myResourceGroupName"
    #>
    param(
        [string]$AzureSubscriptionId = $null,
        [string]$ResourceGroup = $null,
        [string]$DpsName       = $null,
        [string]$IotHubName    = $null
    )

    $TestEnvInfo = [TestEnvironmentInfo]::new()

    # Login to Azure if not already
    $null = & az account show 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Not logged in to Azure. Running 'az login'..."
        & az login --use-device-code
        if ($LASTEXITCODE -ne 0) {
            throw "Azure login failed."
        }
    }
    else {
        Write-Host "Already logged in to Azure."
    }

    $AzureAccount = az account show | ConvertFrom-Json

    # Subscription id...
    if ([string]::IsNullOrWhiteSpace($AzureSubscriptionId)) {
        Stop-OnError -Step "Get Azure account information"
        $AzureSubscriptionId = $AzureAccount.id
    } else {
        $discard = az account set --subscription "$AzureSubscriptionId" --only-show-errors
        Stop-OnError -Step "Set Azure subscription"
    }

    # Required for the IoT Hub and DPS command groups. ADR is reached through ARM directly.
    Install-AzureIotCliExtension

    $AzureResourceGroup = az group show --name "$ResourceGroup" | ConvertFrom-Json

    if ([string]::IsNullOrWhiteSpace($DpsName)) {
        $AzureDpsInstances = az iot dps list --resource-group "$ResourceGroup" | ConvertFrom-Json

        if ($AzureDpsInstances.Count -ne 1) {
            throw "Multiple Azure Device Provisioning services found under resource group $ResourceGroup. Provide DpsName argument to select."
        }

        $AzureDps = $AzureDpsInstances[0]
    } else {
        $AzureDps = az iot dps show --resource-group "$ResourceGroup" --name "$DpsName" | ConvertFrom-Json
    }

    # A DPS linked to an ADR namespace has ADR choosing its provisioning targets, so the hub is
    # reached through the namespace's messaging endpoints rather than the DPS's own linked-hub list.
    $AdrNamespaceId = $AzureDps.properties.deviceRegistry.namespaceResourceId
    if ($null -ne $AdrNamespaceId) {
        $AdrNamespace = Invoke-AzRest -Url "https://management.azure.com$($AdrNamespaceId)?api-version=$($script:AdrApiVersion)"
        $LinkedIotHubNames = @($AdrNamespace.properties.messaging.endpoints.PSObject.Properties | %{ $_.Value.resourceId.Split('/')[-1] })
    } else {
        $LinkedIotHubNames = @($AzureDps.properties.iotHubs | %{ $_.name.Split('.')[0] })
    }

    if ([string]::IsNullOrWhiteSpace($IotHubName)) {
        if ($LinkedIotHubNames.Count -eq 0) {
            throw "Device Provisioning Service ($DpsName) does not have linked IoT hubs"
        }

        $IotHubName = $LinkedIotHubNames[0]
    } elseif ($IotHubName -notin $LinkedIotHubNames) {
        throw "Iot Hub $IotHubName is not linked to $DpsName"
    }

    $AzureIoTHub = az iot hub show --resource-group "$ResourceGroup" --name "$IotHubName" | ConvertFrom-Json

    # Gathering Test Environment settings.
    $TestEnvInfo.AzureResourceGroup = $AzureResourceGroup.name
    $TestEnvInfo.Dps.ResourceGroup = $AzureResourceGroup.name

    if ($null -ne $AdrNamespaceId) {
        # The certificate policy is discovered rather than assumed: it hangs off the issuing CA, and
        # both names are needed to reference it from an enrollment.
        $AdrNamespaceName = $AdrNamespaceId.Split('/')[-1]
        $CertificateAuthorities = Invoke-AzRest -Url "https://management.azure.com$AdrNamespaceId/certificateAuthorities?api-version=$($script:AdrApiVersion)"

        foreach ($CertificateAuthority in $CertificateAuthorities.value) {
            $Policies = Invoke-AzRest -Url "https://management.azure.com$($CertificateAuthority.id)/certificatePolicies?api-version=$($script:AdrApiVersion)"

            if ($Policies.value.Count -gt 0) {
                $TestEnvInfo.AdrPolicy = [AdrPolicyReference]::new($AdrNamespaceName, $CertificateAuthority.name, $Policies.value[0].name)
                $TestEnvInfo.Dps.AdrPolicy = $TestEnvInfo.AdrPolicy
                break
            }
        }
    }

    Write-Host "Getting IoT Hub Connection String"
    $TestEnvInfo.IotHub.ConnectionString = $(az iot hub connection-string show -g $ResourceGroup -n $IotHubName --kt primary --pn iothubowner --query connectionString -o tsv)
    Stop-OnError -Step "Get IoT Hub Connection String"

    Write-Host "Getting IoT Hub's Event Hub Connection String"
    $TestEnvInfo.IotHub.EventHub.ConnectionString = $(az iot hub connection-string show -g $ResourceGroup -n $IotHubName --kt primary --pn iothubowner --eh --query connectionString -o tsv)
    Stop-OnError -Step "Get IoT Hub's Event Hub Connection String"

    $TestEnvInfo.IotHub.EventHub.CompatibleName = $AzureIoTHub.properties.eventHubEndpoints.events.path
    $TestEnvInfo.IotHub.EventHub.PartitionCount = $AzureIoTHub.properties.eventHubEndpoints.events.partitionCount

    Write-Host "Getting IoT Hub's Event Hub Consumer Groups"
    az iot hub consumer-group list --hub-name $IotHubName --resource-group $ResourceGroup | ConvertFrom-Json | %{ $TestEnvInfo.IotHub.EventHub.ConsumerGroups += $_.name }
    Stop-OnError -Step "Get IoT Hub's Event Hub Consumer Groups"

    Write-Host "Retrieving IoT Hub's Device Identities"
    $IotHubDevices = az iot hub device-identity list --hub-name $IotHubName --resource-group $ResourceGroup | ConvertFrom-Json
    Stop-OnError -Step "Retrieve IoT Hub's Device Identities"

    foreach ($Device in $IotHubDevices) {
        if ($Device.authentication.type -eq "sas") {
            $DeviceIdentity = [IotHubSymmetricKeyIdentityInfo]::new(
                $Device.deviceId,
                $Device.authentication.symmetricKey.primaryKey,
                $Device.authentication.symmetricKey.secondaryKey,
                $(az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $Device.deviceId --kt primary --query connectionString -o tsv),
                $(az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $Device.deviceId --kt secondary --query connectionString -o tsv)
            )

            $TestEnvInfo.IotHub.Devices.SymmetricKey += $DeviceIdentity
        } elseif ($Device.authentication.type -eq "x509_thumbprint") {
            $ConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $Device.deviceId | ConvertFrom-Json

            $DeviceIdentity = [IotHubX509IdentityInfo]::new(
                $Device.deviceId,
                $ConnectionString.connectionString,
                [X509CertificateInfo]::new($null, $null), # Certificate and private key retrieval for x509 enrollments would require additional steps, such as downloading the certificate from Azure Key Vault if stored there.
                [X509CertificateInfo]::new($null, $null)
            )

            $TestEnvInfo.IotHub.Devices.X509Thumbprint += $DeviceIdentity
        }
    }

    $TestEnvInfo.Dps.DeviceFqdn = $AzureDps.properties.deviceProvisioningHostName
    $TestEnvInfo.Dps.ServiceFqdn = $AzureDps.properties.serviceOperationsHostName
    $TestEnvInfo.Dps.IdScope = $AzureDps.properties.idScope
    $TestEnvInfo.Dps.LinkedIotHubs += $LinkedIotHubNames

    Write-Host "Getting DPS Connection String"
    $TestEnvInfo.Dps.ConnectionString = $(az iot dps connection-string show -g $ResourceGroup -n $AzureDps.name --kt primary --pn provisioningserviceowner --query connectionString -o tsv)
    Stop-OnError -Step "Get DPS Connection String"

    Write-Host "Retrieving DPS individual enrollments"
    $IndividualEnrollments = az iot dps enrollment list --dps-name $AzureDps.name --resource-group $ResourceGroup | ConvertFrom-Json
    Stop-OnError -Step "Retrieve DPS individual enrollments"

    foreach ($Enrollment in $IndividualEnrollments) {
        if ($Enrollment.attestation.type -eq "symmetricKey") {
            Write-Host "Retrieving DPS individual enrollment ($($Enrollment.registrationId))"
            $IndividualEnrollment = az iot dps enrollment show --dps-name $AzureDps.name --resource-group $ResourceGroup --enrollment-id $($Enrollment.registrationId) --show-keys | ConvertFrom-Json
            Stop-OnError -Step "Retrieve DPS individual enrollment ($($Enrollment.registrationId))"

            $EnrollmentInfo = [DpsSymmetricKeyIndividualEnrollmentInfo]::new(
                $IndividualEnrollment.registrationId,
                $IndividualEnrollment.attestation.symmetricKey.primaryKey,
                $IndividualEnrollment.attestation.symmetricKey.secondaryKey
            )

            $TestEnvInfo.Dps.Enrollments.IndividualSymmetricKey += $EnrollmentInfo
        } elseif ($Enrollment.attestation.type -eq "x509") {
            $EnrollmentInfo = [DpsX509IndividualEnrollmentInfo]::new(
                $Enrollment.registrationId,
                $null # Certificate and private key retrieval for x509 enrollments would require additional steps, such as downloading the certificate from Azure Key Vault if stored there.
            )

            $TestEnvInfo.Dps.Enrollments.IndividualX509 += $EnrollmentInfo
        }
    }

    Write-Host "Retrieving DPS enrollment groups"
    $EnrollmentGroups = az iot dps enrollment-group list --dps-name $AzureDps.name --resource-group $ResourceGroup | ConvertFrom-Json
    Stop-OnError -Step "Retrieve DPS enrollment groups"

    foreach ($EnrollmentGroup in $EnrollmentGroups) {
        if ($EnrollmentGroup.attestation.type -eq "symmetricKey") {
            Write-Host "Retrieving DPS enrollment group ($($EnrollmentGroup.enrollmentGroupId))"
            $SymmetricKeyEnrollmentGroup = az iot dps enrollment-group show --dps-name $AzureDps.name --resource-group $ResourceGroup --group-id $($EnrollmentGroup.enrollmentGroupId) --show-keys | ConvertFrom-Json
            Stop-OnError -Step "Retrieve DPS enrollment group ($($EnrollmentGroup.enrollmentGroupId))"

            $EnrollmentGroupInfo = [DpsSymmetricKeyEnrollmentGroupInfo]::new(
                $SymmetricKeyEnrollmentGroup.enrollmentGroupId,
                $SymmetricKeyEnrollmentGroup.attestation.symmetricKey.primaryKey,
                $SymmetricKeyEnrollmentGroup.attestation.symmetricKey.secondaryKey
            )

            $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey += $EnrollmentGroupInfo
        } elseif ($EnrollmentGroup.attestation.type -eq "x509") {
            $EnrollmentGroupInfo = [DpsX509EnrollmentGroupInfo]::new(
                $EnrollmentGroup.enrollmentGroupId,
                $null # Certificate and private key retrieval for x509 enrollments would require additional steps, such as downloading the certificate from Azure Key Vault if stored there.
            )

            $TestEnvInfo.Dps.Enrollments.GroupX509 += $EnrollmentGroupInfo
        }
    }

    return $TestEnvInfo    
}

function ConvertFrom-JsonToTestEnvironmentInfo {
    param(
        [string]$JsonString
    )

    return [TestEnvironmentInfo]::FromJson($JsonString)
}

function New-AzIotCSDKE2ETestConfig {
    param(
        [TestEnvironmentInfo]$TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$Target = "bash",
        [string]$OutFile
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./azure-iot-sdk-c-e2e-test-config"
        if ($Target -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    $IotHubDeviceCertificateBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.IotHub.Devices.X509Thumbprint[0].PrimaryCertificate.ToPem())
    $IotHubDevicePrivateKeyBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.IotHub.Devices.X509Thumbprint[0].PrimaryCertificate.PrivateKey.ToRsaPkcs1Pem())
    $IotHubDeviceCertificateThumbprint = $($TestEnvInfo.IotHub.Devices.X509Thumbprint[0].PrimaryCertificate.GetThumbprint())

    $DpsCertificateBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.Dps.Enrollments.IndividualX509[0].Certificate.ToPem())
    $DpsPrivateKeyBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.Dps.Enrollments.IndividualX509[0].Certificate.PrivateKey.ToRsaPkcs1Pem())
    $DpsRegistrationId = $($TestEnvInfo.Dps.Enrollments.IndividualX509[0].Id)

    # Root CA certificate for CSR/ADR tests (create one if not already present)
    if ($TestEnvInfo.Dps.RootCaCertificates.Count -eq 0) {
        $TestEnvInfo.Dps.AddRootCaCertificate() | Out-Null
    }
    $DpsRootCACertificateBase64 = ConvertTo-Base64 -Content $($TestEnvInfo.Dps.RootCaCertificates[0].ToPem())
    $DpsRootCAPrivateKeyBase64 = ConvertTo-Base64 -Content $($TestEnvInfo.Dps.RootCaCertificates[0].PrivateKey.ToRsaPkcs1Pem())

    # Symmetric key group enrollment (optional)
    $SymmKeyGroupEnrollmentId = $null
    $SymmKeyGroupPrimaryKey = $null
    if ($TestEnvInfo.Dps.Enrollments.GroupSymmetricKey.Count -gt 0) {
        $SymmKeyGroupEnrollmentId = $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey[0].Id
        $SymmKeyGroupPrimaryKey = $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey[0].PrimaryKey
    }

    # Emit EVERY DPS x509 individual enrollment, indexed by position, so parallel
    # test legs (e.g. the Windows and Linux jobs of one workflow run) can each
    # claim a DISTINCT device and never collide on a single shared device twin.
    # The unsuffixed IOT_DPS_INDIVIDUAL_* vars above are kept (they equal index 0)
    # for backward compatibility with consumers that expect a single device.
    $DpsIndividualEnrollments = @($TestEnvInfo.Dps.Enrollments.IndividualX509)
    $DpsIndividualCount = $DpsIndividualEnrollments.Count
    $DpsIndividualIndexedLines = @()
    for ($i = 0; $i -lt $DpsIndividualCount; $i++) {
        $Enrollment = $DpsIndividualEnrollments[$i]
        $EnrollmentCertB64 = ConvertTo-Base64 -Content $Enrollment.Certificate.ToPem()
        $EnrollmentKeyB64 = ConvertTo-Base64 -Content $Enrollment.Certificate.PrivateKey.ToRsaPkcs1Pem()
        $EnrollmentRegId = $Enrollment.Id
        if ($Target -eq "powershell") {
            $DpsIndividualIndexedLines += "`$env:IOT_DPS_INDIVIDUAL_X509_CERTIFICATE_$i = `"$EnrollmentCertB64`""
            $DpsIndividualIndexedLines += "`$env:IOT_DPS_INDIVIDUAL_X509_KEY_$i = `"$EnrollmentKeyB64`""
            $DpsIndividualIndexedLines += "`$env:IOT_DPS_INDIVIDUAL_REGISTRATION_ID_$i = `"$EnrollmentRegId`""
        } else {
            $DpsIndividualIndexedLines += "export IOT_DPS_INDIVIDUAL_X509_CERTIFICATE_$i=`"$EnrollmentCertB64`""
            $DpsIndividualIndexedLines += "export IOT_DPS_INDIVIDUAL_X509_KEY_$i=`"$EnrollmentKeyB64`""
            $DpsIndividualIndexedLines += "export IOT_DPS_INDIVIDUAL_REGISTRATION_ID_$i=`"$EnrollmentRegId`""
        }
    }

    if ($Target -eq "powershell") {
        $Lines = @(
            "`$env:IOTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOTHUB_EVENTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "`$env:IOTHUB_EVENTHUB_LISTEN_NAME = `"$($TestEnvInfo.IotHub.EventHub.CompatibleName)`""
            "`$env:IOTHUB_PARTITION_COUNT = $($TestEnvInfo.IotHub.EventHub.PartitionCount)"
            "`$env:IOT_DPS_GLOBAL_ENDPOINT = `"$($TestEnvInfo.Dps.DeviceFqdn)`""
            "`$env:IOT_DPS_CONNECTION_STRING = `"$($TestEnvInfo.Dps.ConnectionString)`""
            "`$env:IOT_DPS_ID_SCOPE = `"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:IOTHUB_DEVICE_CONN_STRING_INVALIDCERT = `"HostName=invalidcertiothub1.westus.cloudapp.azure.com;DeviceId=DoNotDelete1;SharedAccessKey=zWmeTGWmjcgDG1dpuSCVjc5ZY4TqVnKso5+g1wt/K3E=`""
            "`$env:IOTHUB_CONN_STRING_INVALIDCERT = `"HostName=invalidcertiothub1.westus.cloudapp.azure.com;SharedAccessKeyName=iothubowner;SharedAccessKey=Fk1H0asPeeAwlRkUMTybJasksTYTd13cgI7SsteB05U=`""
            "`$env:DPS_GLOBALDEVICEENDPOINT_INVALIDCERT = `"invalidcertgde1.westus.cloudapp.azure.com`""
            "`$env:PROVISIONING_CONNECTION_STRING_INVALIDCERT = `"HostName=invalidcertdps1.westus.cloudapp.azure.com;SharedAccessKeyName=provisioningserviceowner;SharedAccessKey=lGO7OlXNhXlFyYV1rh9F/lUCQC1Owuh5f/1P0I1AFSY=`""
            "`$env:IOTHUB_E2E_X509_CERT_BASE64 = `"$IotHubDeviceCertificateBase64`""
            "`$env:IOTHUB_E2E_X509_PRIVATE_KEY_BASE64 = `"$IotHubDevicePrivateKeyBase64`""
            "`$env:IOTHUB_E2E_X509_THUMBPRINT = `"$IotHubDeviceCertificateThumbprint`""
            "`$env:IOT_DPS_INDIVIDUAL_X509_CERTIFICATE = `"$DpsCertificateBase64`""
            "`$env:IOT_DPS_INDIVIDUAL_X509_KEY = `"$DpsPrivateKeyBase64`""
            "`$env:IOT_DPS_INDIVIDUAL_REGISTRATION_ID = `"$DpsRegistrationId`""
            "`$env:IOT_DPS_INDIVIDUAL_COUNT = $DpsIndividualCount"
            $DpsIndividualIndexedLines
            "`$env:PROVISIONING_ROOT_CERT = `"$DpsRootCACertificateBase64`""
            "`$env:PROVISIONING_ROOT_CERT_KEY = `"$DpsRootCAPrivateKeyBase64`""
            "`$env:ADR_CERT_MGMT_NAMESPACE_NAME = `"$($TestEnvInfo.AdrPolicy.NamespaceName)`""
            "`$env:ADR_CERT_MGMT_CERTIFICATE_AUTHORITY_NAME = `"$($TestEnvInfo.AdrPolicy.CertificateAuthorityName)`""
            "`$env:ADR_CERT_MGMT_POLICY_NAME = `"$($TestEnvInfo.AdrPolicy.CertificatePolicyName)`""
            $(if ($SymmKeyGroupEnrollmentId) { "`$env:IOT_DPS_SYMM_KEY_GROUP_ENROLLMENT_ID = `"$SymmKeyGroupEnrollmentId`"" })
            $(if ($SymmKeyGroupPrimaryKey) { "`$env:IOT_DPS_SYMM_KEY_GROUP_PRIMARY_KEY = `"$SymmKeyGroupPrimaryKey`"" })
            "`$env:AZURE_RESOURCE_GROUP = `"$($TestEnvInfo.AzureResourceGroup)`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export IOTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOTHUB_EVENTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "export IOTHUB_EVENTHUB_LISTEN_NAME=`"$($TestEnvInfo.IotHub.EventHub.CompatibleName)`""
            "export IOTHUB_PARTITION_COUNT=$($TestEnvInfo.IotHub.EventHub.PartitionCount)"
            "export IOT_DPS_GLOBAL_ENDPOINT=`"$($TestEnvInfo.Dps.DeviceFqdn)`""
            "export IOT_DPS_CONNECTION_STRING=`"$($TestEnvInfo.Dps.ConnectionString)`""
            "export IOT_DPS_ID_SCOPE=`"$($TestEnvInfo.Dps.IdScope)`""
            "export IOTHUB_DEVICE_CONN_STRING_INVALIDCERT=`"HostName=invalidcertiothub1.westus.cloudapp.azure.com;DeviceId=DoNotDelete1;SharedAccessKey=zWmeTGWmjcgDG1dpuSCVjc5ZY4TqVnKso5+g1wt/K3E=`""
            "export IOTHUB_CONN_STRING_INVALIDCERT=`"HostName=invalidcertiothub1.westus.cloudapp.azure.com;SharedAccessKeyName=iothubowner;SharedAccessKey=Fk1H0asPeeAwlRkUMTybJasksTYTd13cgI7SsteB05U=`""
            "export DPS_GLOBALDEVICEENDPOINT_INVALIDCERT=`"invalidcertgde1.westus.cloudapp.azure.com`""
            "export PROVISIONING_CONNECTION_STRING_INVALIDCERT=`"HostName=invalidcertdps1.westus.cloudapp.azure.com;SharedAccessKeyName=provisioningserviceowner;SharedAccessKey=lGO7OlXNhXlFyYV1rh9F/lUCQC1Owuh5f/1P0I1AFSY=`""
            "export IOTHUB_E2E_X509_CERT_BASE64=`"$IotHubDeviceCertificateBase64`""
            "export IOTHUB_E2E_X509_PRIVATE_KEY_BASE64=`"$IotHubDevicePrivateKeyBase64`""
            "export IOTHUB_E2E_X509_THUMBPRINT=`"$IotHubDeviceCertificateThumbprint`""
            "export IOT_DPS_INDIVIDUAL_X509_CERTIFICATE=`"$DpsCertificateBase64`""
            "export IOT_DPS_INDIVIDUAL_X509_KEY=`"$DpsPrivateKeyBase64`""
            "export IOT_DPS_INDIVIDUAL_REGISTRATION_ID=`"$DpsRegistrationId`""
            "export IOT_DPS_INDIVIDUAL_COUNT=$DpsIndividualCount"
            $DpsIndividualIndexedLines
            "export PROVISIONING_ROOT_CERT=`"$DpsRootCACertificateBase64`""
            "export PROVISIONING_ROOT_CERT_KEY=`"$DpsRootCAPrivateKeyBase64`""
            "export ADR_CERT_MGMT_NAMESPACE_NAME=`"$($TestEnvInfo.AdrPolicy.NamespaceName)`""
            "export ADR_CERT_MGMT_CERTIFICATE_AUTHORITY_NAME=`"$($TestEnvInfo.AdrPolicy.CertificateAuthorityName)`""
            "export ADR_CERT_MGMT_POLICY_NAME=`"$($TestEnvInfo.AdrPolicy.CertificatePolicyName)`""
            $(if ($SymmKeyGroupEnrollmentId) { "export IOT_DPS_SYMM_KEY_GROUP_ENROLLMENT_ID=`"$SymmKeyGroupEnrollmentId`"" })
            $(if ($SymmKeyGroupPrimaryKey) { "export IOT_DPS_SYMM_KEY_GROUP_PRIMARY_KEY=`"$SymmKeyGroupPrimaryKey`"" })
            "export AZURE_RESOURCE_GROUP=`"$($TestEnvInfo.AzureResourceGroup)`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "End-to-End test configuration written to $OutFile"

    return $OutFile

    # Cut list?
        #   IOTHUB_POLICY_KEY: $(IOTHUB-POLICY-KEY) OJdGPkx9HgWecCSECw7D7Hv8AuiKE+A7TWjAcEUv5tk=
        #   IOTHUB_CA_ROOT_CERT: $(IOTHUB-CA-ROOT-CERT)
        #   IOTHUB_CA_ROOT_CERT_KEY: $(IOTHUB-CA-ROOT-CERT-KEY)
}

function New-AzIotNetSDKE2ETestConfig {
    param(
        [TestEnvironmentInfo]$TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$Target = "bash",
        [string]$OutFile
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./azure-iot-sdk-net-e2e-test-config"
        if ($Target -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    $IotHubDeviceCertificateBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.IotHub.Devices.X509Thumbprint[0].PrimaryCertificate.ToPem())
    $IotHubDevicePrivateKeyBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.IotHub.Devices.X509Thumbprint[0].PrimaryCertificate.PrivateKey.ToPem())
    $IotHubDeviceCertificateThumbprint = $($TestEnvInfo.IotHub.Devices.X509Thumbprint[0].PrimaryCertificate.GetThumbprint())

    $DpsCertificateBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.Dps.Enrollments.IndividualX509[0].Certificate.ToPem())
    $DpsPrivateKeyBase64 = $(ConvertTo-Base64 -Content $TestEnvInfo.Dps.Enrollments.IndividualX509[0].Certificate.PrivateKey.ToPem())
    $DpsRegistrationId = $($TestEnvInfo.Dps.Enrollments.IndividualX509[0].Id)

    # Root CA certificate for CSR/ADR tests (create one if not already present)
    if ($TestEnvInfo.Dps.RootCaCertificates.Count -eq 0) {
        $TestEnvInfo.Dps.AddRootCaCertificate() | Out-Null
    }
    $DpsRootCACertificateBase64 = ConvertTo-Base64 -Content $($TestEnvInfo.Dps.RootCaCertificates[0].ToPem())
    $DpsRootCAPrivateKeyBase64 = ConvertTo-Base64 -Content $($TestEnvInfo.Dps.RootCaCertificates[0].PrivateKey.ToPem())

    # Symmetric key group enrollment (optional)
    $SymmKeyGroupEnrollmentId = $null
    $SymmKeyGroupPrimaryKey = $null
    if ($TestEnvInfo.Dps.Enrollments.GroupSymmetricKey.Count -gt 0) {
        $SymmKeyGroupEnrollmentId = $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey[0].Id
        $SymmKeyGroupPrimaryKey = $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey[0].PrimaryKey
    }

    if ($Target -eq "powershell") {
        $Lines = @(
            "`$env:IOTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOT_DPS_GLOBAL_ENDPOINT = `"$($TestEnvInfo.Dps.DeviceFqdn)`""
            "`$env:IOT_DPS_CONNECTION_STRING = `"$($TestEnvInfo.Dps.ConnectionString)`""
            "`$env:IOT_DPS_ID_SCOPE = `"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:IOTHUB_E2E_X509_CERT_BASE64 = `"$IotHubDeviceCertificateBase64`""
            "`$env:IOTHUB_E2E_X509_PRIVATE_KEY_BASE64 = `"$IotHubDevicePrivateKeyBase64`""
            "`$env:IOTHUB_E2E_X509_THUMBPRINT = `"$IotHubDeviceCertificateThumbprint`""
            "`$env:IOT_DPS_INDIVIDUAL_X509_CERTIFICATE = `"$DpsCertificateBase64`""
            "`$env:IOT_DPS_INDIVIDUAL_X509_KEY = `"$DpsPrivateKeyBase64`""
            "`$env:IOT_DPS_INDIVIDUAL_REGISTRATION_ID = `"$DpsRegistrationId`""
            "`$env:PROVISIONING_ROOT_CERT = `"$DpsRootCACertificateBase64`""
            "`$env:PROVISIONING_ROOT_CERT_KEY = `"$DpsRootCAPrivateKeyBase64`""
            "`$env:ADR_CERT_MGMT_NAMESPACE_NAME = `"$($TestEnvInfo.AdrPolicy.NamespaceName)`""
            "`$env:ADR_CERT_MGMT_CERTIFICATE_AUTHORITY_NAME = `"$($TestEnvInfo.AdrPolicy.CertificateAuthorityName)`""
            "`$env:ADR_CERT_MGMT_POLICY_NAME = `"$($TestEnvInfo.AdrPolicy.CertificatePolicyName)`""
            $(if ($SymmKeyGroupEnrollmentId) { "`$env:IOT_DPS_SYMM_KEY_GROUP_ENROLLMENT_ID = `"$SymmKeyGroupEnrollmentId`"" })
            $(if ($SymmKeyGroupPrimaryKey) { "`$env:IOT_DPS_SYMM_KEY_GROUP_PRIMARY_KEY = `"$SymmKeyGroupPrimaryKey`"" })
            "`$env:AZURE_RESOURCE_GROUP = `"$($TestEnvInfo.AzureResourceGroup)`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export IOTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOT_DPS_GLOBAL_ENDPOINT=`"$($TestEnvInfo.Dps.DeviceFqdn)`""
            "export IOT_DPS_CONNECTION_STRING=`"$($TestEnvInfo.Dps.ConnectionString)`""
            "export IOT_DPS_ID_SCOPE=`"$($TestEnvInfo.Dps.IdScope)`""
            "export IOTHUB_E2E_X509_CERT_BASE64=`"$IotHubDeviceCertificateBase64`""
            "export IOTHUB_E2E_X509_PRIVATE_KEY_BASE64=`"$IotHubDevicePrivateKeyBase64`""
            "export IOTHUB_E2E_X509_THUMBPRINT=`"$IotHubDeviceCertificateThumbprint`""
            "export IOT_DPS_INDIVIDUAL_X509_CERTIFICATE=`"$DpsCertificateBase64`""
            "export IOT_DPS_INDIVIDUAL_X509_KEY=`"$DpsPrivateKeyBase64`""
            "export IOT_DPS_INDIVIDUAL_REGISTRATION_ID=`"$DpsRegistrationId`""
            "export PROVISIONING_ROOT_CERT=`"$DpsRootCACertificateBase64`""
            "export PROVISIONING_ROOT_CERT_KEY=`"$DpsRootCAPrivateKeyBase64`""
            "export ADR_CERT_MGMT_NAMESPACE_NAME=`"$($TestEnvInfo.AdrPolicy.NamespaceName)`""
            "export ADR_CERT_MGMT_CERTIFICATE_AUTHORITY_NAME=`"$($TestEnvInfo.AdrPolicy.CertificateAuthorityName)`""
            "export ADR_CERT_MGMT_POLICY_NAME=`"$($TestEnvInfo.AdrPolicy.CertificatePolicyName)`""
            $(if ($SymmKeyGroupEnrollmentId) { "export IOT_DPS_SYMM_KEY_GROUP_ENROLLMENT_ID=`"$SymmKeyGroupEnrollmentId`"" })
            $(if ($SymmKeyGroupPrimaryKey) { "export IOT_DPS_SYMM_KEY_GROUP_PRIMARY_KEY=`"$SymmKeyGroupPrimaryKey`"" })
            "export AZURE_RESOURCE_GROUP=`"$($TestEnvInfo.AzureResourceGroup)`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "End-to-End test configuration written to $OutFile"

    return $OutFile
}

function New-AzIotPythonSDKE2ETestConfig {
    param(
        [TestEnvironmentInfo]$TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$Target = "bash",
        [string]$OutFile
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./azure-iot-sdk-python-e2e-test-config"
        if ($Target -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    if ($TestEnvInfo.Dps.RootCaCertificates.Count -eq 0) {
        $TestEnvInfo.Dps.AddRootCaCertificate() | Out-Null
    }

    $DpsRootCACertificateBase64 = ConvertTo-Base64 -Content $($TestEnvInfo.Dps.RootCaCertificates[0].ToPem())
    $DpsRootCAPrivateKeyBase64 = ConvertTo-Base64 -Content $($TestEnvInfo.Dps.RootCaCertificates[0].PrivateKey.ToPem())

    if ($Target -eq "powershell") {
        $Lines = @(
            "`$env:IOTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOTHUB_E2E_IOTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOTHUB_EVENTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "`$env:IOTHUB_E2E_EVENTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "`$env:EVENTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "`$env:IOTHUB_E2E_EVENTHUB_CONSUMER_GROUP = `"``$($TestEnvInfo.IotHub.EventHub.ConsumerGroups[0])`""
            "`$env:EVENTHUB_CONSUMER_GROUP = `"``$($TestEnvInfo.IotHub.EventHub.ConsumerGroups[0])`""

            "`$env:PROVISIONING_DEVICE_IDSCOPE = `"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:PROVISIONING_IDSCOPE = `"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:PROVISIONING_DEVICE_ENDPOINT = `"$($TestEnvInfo.Dps.DeviceFqdn)`""
            "`$env:PROVISIONING_HOST = `"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:PROVISIONING_SERVICE_CONNECTION_STRING = `"$($TestEnvInfo.Dps.ConnectionString)`""

            "`$env:PROVISIONING_ROOT_CERT = `"$DpsRootCACertificateBase64`""
            "`$env:PROVISIONING_ROOT_CERT_KEY = `"$DpsRootCAPrivateKeyBase64`""
            "`$env:PROVISIONING_ROOT_PASSWORD = `"`""

            "`$env:ADR_CERT_MGMT_NAMESPACE_NAME = `"$($TestEnvInfo.AdrPolicy.NamespaceName)`""
            "`$env:ADR_CERT_MGMT_CERTIFICATE_AUTHORITY_NAME = `"$($TestEnvInfo.AdrPolicy.CertificateAuthorityName)`""
            "`$env:ADR_CERT_MGMT_POLICY_NAME = `"$($TestEnvInfo.AdrPolicy.CertificatePolicyName)`""

            "`$env:PYTHONUNBUFFERED = `"True`""

            "`$env:AZURE_RESOURCE_GROUP = `"$($TestEnvInfo.AzureResourceGroup)`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export IOTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOTHUB_E2E_IOTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOTHUB_EVENTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "export IOTHUB_E2E_EVENTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "export EVENTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "export IOTHUB_E2E_EVENTHUB_CONSUMER_GROUP=`"`\$($TestEnvInfo.IotHub.EventHub.ConsumerGroups[0])`""
            "export EVENTHUB_CONSUMER_GROUP=`"`\$($TestEnvInfo.IotHub.EventHub.ConsumerGroups[0])`""


            "export PROVISIONING_DEVICE_IDSCOPE=`"$($TestEnvInfo.Dps.IdScope)`""
            "export PROVISIONING_IDSCOPE=`"$($TestEnvInfo.Dps.IdScope)`""
            "export PROVISIONING_DEVICE_ENDPOINT=`"$($TestEnvInfo.Dps.DeviceFqdn)`""
            "export PROVISIONING_HOST=`"$($TestEnvInfo.Dps.IdScope)`""
            "export PROVISIONING_SERVICE_CONNECTION_STRING=`"$($TestEnvInfo.Dps.ConnectionString)`""

            "export PROVISIONING_ROOT_CERT=`"$DpsRootCACertificateBase64`""
            "export PROVISIONING_ROOT_CERT_KEY=`"$DpsRootCAPrivateKeyBase64`""
            "export PROVISIONING_ROOT_PASSWORD=`"`""

            "export ADR_CERT_MGMT_NAMESPACE_NAME=`"$($TestEnvInfo.AdrPolicy.NamespaceName)`""
            "export ADR_CERT_MGMT_CERTIFICATE_AUTHORITY_NAME=`"$($TestEnvInfo.AdrPolicy.CertificateAuthorityName)`""
            "export ADR_CERT_MGMT_POLICY_NAME=`"$($TestEnvInfo.AdrPolicy.CertificatePolicyName)`""

            "export PYTHONUNBUFFERED=`"True`""

            "export AZURE_RESOURCE_GROUP=`"$($TestEnvInfo.AzureResourceGroup)`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "End-to-End test configuration written to $OutFile"

    return $OutFile
}

function New-AzIotPythonSdkSampleConfig {
    param(
        [TestEnvironmentInfo]$TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$TargetEnvironment = "bash",
        [string]$DeviceId = "device-" + $(Get-Random -Minimum 100000 -Maximum 999999),
        [string]$OutFile = $null,
        [string]$CertificatesDir = "$(pwd)/certs",
        [string]$PrivateKeyDir = "$(pwd)/private"
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./azure-iot-sdk-python-sample-config"
        if ($TargetEnvironment -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    if ($TestEnvInfo.Dps.Enrollments.GroupX509.Count -eq 0) {
        $TestEnvInfo.Dps.AddX509GroupEnrollment("group1") | Out-Null
    }

    $X509EnrollmentGroupIdentity = $TestEnvInfo.Dps.Enrollments.GroupX509[0].AddIdentity($DeviceId, [timespan]::FromDays(365))

    $DeviceDpsX509PrivateKeyFile = "$PrivateKeyDir/$DeviceId.key.pem"    
    $X509EnrollmentGroupIdentity.Certificate.PrivateKey.ExportToPemFile($DeviceDpsX509PrivateKeyFile)

    $DeviceDpsX509CertificateChainPem = $X509EnrollmentGroupIdentity.Certificate.ToPem()
    $DeviceDpsX509CertificateChainPem += "`n" +  $TestEnvInfo.Dps.Enrollments.GroupX509[0].Certificate.ToPem()
    $DeviceDpsX509CertificateChainPem += "`n" +  $TestEnvInfo.Dps.RootCaCertificates[0].ToPem()

    $DeviceDpsX509CertificateChainFile = "$CertificatesDir/$DeviceId-full-chain.cert.pem"
    Set-FileContent -Path $DeviceDpsX509CertificateChainFile -Content $DeviceDpsX509CertificateChainPem

    $CsrPrivateKeyFile = "$PrivateKeyDir/$DeviceId-dps-csr-private-key.pem"
    $ProvisioningIssuedCertFile = "$CertificatesDir/$DeviceId-dps-csr-issued-cert.pem"
    $IothubIssuedCertFile = "$CertificatesDir/$DeviceId-iot-csr-issued-cert.pem"
    
    $CsrPrivateKey = New-EcdsaPrivateKey -Path $CsrPrivateKeyFile
    $ProvisioningCsr = $(New-X509CertificateSigningRequest -Subject $DeviceId -Key $CsrPrivateKey -NoHeaders)
    $IothubCsr = $(New-X509CertificateSigningRequest -Subject $DeviceId -Key $CsrPrivateKey -NoHeaders)
    
    if ($TargetEnvironment -eq "powershell") {
        $Lines = @(
            "`$env:PROVISIONING_HOST=`"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:PROVISIONING_IDSCOPE=`"$($TestEnvInfo.Dps.IdScope)`""
            "`$env:PROVISIONING_REGISTRATION_ID=`"$DeviceId`""

            "`$env:PROVISIONING_X509_CERT_FILE=`"$DeviceDpsX509CertificateChainFile`""
            "`$env:PROVISIONING_X509_KEY_FILE=`"$DeviceDpsX509PrivateKeyFile`""

            "`$env:PROVISIONING_CSR_KEY_FILE=`"$CsrPrivateKeyFile`""
            "`$env:PROVISIONING_CSR=`"$ProvisioningCsr`""
            "`$env:PROVISIONING_ISSUED_CERT_FILE=`"$ProvisioningIssuedCertFile`""

            "`$env:IOTHUB_CSR=`"$IothubCsr`""
            "`$env:IOTHUB_ISSUED_CERT_FILE=`"$IothubIssuedCertFile`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export PROVISIONING_HOST=`"$($TestEnvInfo.Dps.IdScope)`""
            "export PROVISIONING_IDSCOPE=`"$($TestEnvInfo.Dps.IdScope)`""
            "export PROVISIONING_REGISTRATION_ID=`"$DeviceId`""

            "export PROVISIONING_X509_CERT_FILE=`"$DeviceDpsX509CertificateChainFile`""
            "export PROVISIONING_X509_KEY_FILE=`"$DeviceDpsX509PrivateKeyFile`""

            "export PROVISIONING_CSR_KEY_FILE=`"$CsrPrivateKeyFile`""
            "export PROVISIONING_CSR=`"$ProvisioningCsr`""
            "export PROVISIONING_ISSUED_CERT_FILE=`"$ProvisioningIssuedCertFile`""

            "export IOTHUB_CSR=`"$IothubCsr`""
            "export IOTHUB_ISSUED_CERT_FILE=`"$IothubIssuedCertFile`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "End-to-End test configuration written to $OutFile"

    return $OutFile
}

function New-AzIotuAmqpE2ETestConfig {
    <#
    .SYNOPSIS
    Creates a test configuration script for azure-uamqp-c's iothub_e2e test.

    .DESCRIPTION
    Generates a bash or PowerShell script that exports the environment
    variables required by the iothub_e2e test in azure-uamqp-c:
        IOTHUB_CONNECTION_STRING        - service connection string to the IoT Hub
        UAMQP_E2E_DEVICE_KEY            - primary symmetric key of an IoT Hub
                                          device named "eh_testdevice" (the
                                          device id is hard-coded in the test)
        IOTHUB_EVENTHUB_CONNECTION_STRING / IOTHUB_EVENTHUB_LISTEN_NAME /
        IOTHUB_PARTITION_COUNT          - event hub built-in endpoint info
        AZURE_RESOURCE_GROUP            - the resource group hosting the hub

    The function ensures an IoT Hub symmetric-key device with the requested
    DeviceId exists (creating it via 'az iot hub device-identity create' if it
    is not already present in the supplied TestEnvironmentInfo) and emits its
    primary key into the generated script.

    .PARAMETER TestEnvInfo
    The TestEnvironmentInfo object returned by New-AzIotTestEnvironment.

    .PARAMETER Target
    The target script format: 'bash' or 'powershell'. Default is 'bash'.

    .PARAMETER OutFile
    The output file path. If not specified, a default name is used.

    .PARAMETER DeviceId
    The IoT Hub device identifier whose primary key is exported as
    UAMQP_E2E_DEVICE_KEY. Defaults to "eh_testdevice", which is the id
    hard-coded in azure-uamqp-c/tests/iothub_e2e/iothub_e2e.c.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotTestEnvironment -NoDps
    PS> New-AzIotuAmqpE2ETestConfig -TestEnvInfo $TestEnvInfo -Target bash -OutFile test_config/set_e2e_test_env_vars.sh
    #>
    param(
        [TestEnvironmentInfo]$TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$Target = "bash",
        [string]$OutFile,
        [string]$DeviceId = "eh_testdevice"
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./azure-uamqp-c-e2e-test-config"
        if ($Target -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    # Parse the IoT Hub resource name out of the service connection string.
    # Format: HostName=<hub>.<suffix>;SharedAccessKeyName=<name>;SharedAccessKey=<key>
    $HostNamePair = ($TestEnvInfo.IotHub.ConnectionString -split ';' | Where-Object { $_ -like 'HostName=*' } | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($HostNamePair)) {
        throw "Could not parse HostName from IoT Hub connection string."
    }
    $HostName = $HostNamePair -replace '^HostName=', ''
    $IotHubName = $HostName.Split('.')[0]
    $ResourceGroup = $TestEnvInfo.AzureResourceGroup

    # Reuse a previously-provisioned device with the requested id if present;
    # otherwise create one and store it on TestEnvInfo so subsequent callers
    # (including persisted JSON snapshots) can find it.
    $Device = $TestEnvInfo.IotHub.Devices.SymmetricKey | Where-Object { $_.Id -eq $DeviceId } | Select-Object -First 1
    if ($null -eq $Device) {
        Write-Host "Creating Azure IoT Hub symmetric-key device ($DeviceId)"
        $IotHubDeviceInfo = az iot hub device-identity create --resource-group $ResourceGroup --hub-name $IotHubName --device-id $DeviceId | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub symmetric-key device ($DeviceId)"
        $PrimaryConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $DeviceId --kt primary | ConvertFrom-Json
        Stop-OnError -Step "Get Azure IoT Hub device primary connection-string ($DeviceId)"
        $SecondaryConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $DeviceId --kt secondary | ConvertFrom-Json
        Stop-OnError -Step "Get Azure IoT Hub device secondary connection-string ($DeviceId)"

        $Device = [IotHubSymmetricKeyIdentityInfo]::new(
            $DeviceId,
            $IotHubDeviceInfo.authentication.symmetricKey.primaryKey,
            $IotHubDeviceInfo.authentication.symmetricKey.secondaryKey,
            $PrimaryConnectionString.connectionString,
            $SecondaryConnectionString.connectionString
        )

        $TestEnvInfo.IotHub.Devices.SymmetricKey += $Device
    }

    if ($Target -eq "powershell") {
        $Lines = @(
            "`$env:IOTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOTHUB_EVENTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "`$env:IOTHUB_EVENTHUB_LISTEN_NAME = `"$($TestEnvInfo.IotHub.EventHub.CompatibleName)`""
            "`$env:IOTHUB_PARTITION_COUNT = $($TestEnvInfo.IotHub.EventHub.PartitionCount)"
            "`$env:IOTHUB_E2E_DEVICE_ID = `"$($Device.Id)`""
            "`$env:UAMQP_E2E_DEVICE_KEY = `"$($Device.PrimaryKey)`""
            "`$env:AZURE_RESOURCE_GROUP = `"$($TestEnvInfo.AzureResourceGroup)`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export IOTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOTHUB_EVENTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "export IOTHUB_EVENTHUB_LISTEN_NAME=`"$($TestEnvInfo.IotHub.EventHub.CompatibleName)`""
            "export IOTHUB_PARTITION_COUNT=$($TestEnvInfo.IotHub.EventHub.PartitionCount)"
            "export IOTHUB_E2E_DEVICE_ID=`"$($Device.Id)`""
            "export UAMQP_E2E_DEVICE_KEY=`"$($Device.PrimaryKey)`""
            "export AZURE_RESOURCE_GROUP=`"$($TestEnvInfo.AzureResourceGroup)`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "uAMQP E2E test configuration written to $OutFile"

    return $OutFile
}

function New-AzIotHortonTestConfig {
    <#
    .SYNOPSIS
    Creates a Horton test configuration script with the environment variables needed by the Horton test framework.

    .DESCRIPTION
    Generates a bash or PowerShell script that exports the environment variables required by Horton,
    including the IoT Hub connection string and Azure Container Registry credentials.

    .PARAMETER TestEnvInfo
    The TestEnvironmentInfo object returned by New-AzIotTestEnvironment (with -AddContainerRegistry).

    .PARAMETER Target
    The target script format: 'bash' or 'powershell'. Default is 'bash'.

    .PARAMETER OutFile
    The output file path. If not specified, a default name is used.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotTestEnvironment -NoDps -AddContainerRegistry
    PS> New-AzIotHortonTestConfig -TestEnvInfo $TestEnvInfo -Target bash -OutFile test_config/set_horton_env_vars.sh
    #>
    param(
        $TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$Target = "bash",
        [string]$OutFile
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./horton-test-config"
        if ($Target -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    $AcrLoginServer = $TestEnvInfo.ContainerRegistry[0].LoginServer
    $AcrUsername = $TestEnvInfo.ContainerRegistry[0].Username
    $AcrPassword = $TestEnvInfo.ContainerRegistry[0].Password

    if ($Target -eq "powershell") {
        $Lines = @(
            "`$env:IOTHUB_E2E_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOTHUB_E2E_EVENTHUB_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "`$env:IOTHUB_E2E_REPO_ADDRESS = `"$AcrLoginServer`""
            "`$env:IOTHUB_E2E_REPO_USER = `"$AcrUsername`""
            "`$env:IOTHUB_E2E_REPO_PASSWORD = `"$AcrPassword`""
            "`$env:AZURE_RESOURCE_GROUP = `"$($TestEnvInfo.AzureResourceGroup)`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export IOTHUB_E2E_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOTHUB_E2E_EVENTHUB_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.EventHub.ConnectionString)`""
            "export IOTHUB_E2E_REPO_ADDRESS=`"$AcrLoginServer`""
            "export IOTHUB_E2E_REPO_USER=`"$AcrUsername`""
            "export IOTHUB_E2E_REPO_PASSWORD=`"$AcrPassword`""
            "export AZURE_RESOURCE_GROUP=`"$($TestEnvInfo.AzureResourceGroup)`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "Horton test configuration written to $OutFile"

    return $OutFile
}


# <[Submodule Consistency Check]>

# --- GitHub API helpers ---

function Get-SubmoduleCheckGitHubHeaders {
    param([string]$Token)

    $headers = @{
        "User-Agent" = "check-submodule-consistency/1.0"
        "Accept"     = "application/vnd.github.v3+json"
    }
    if ($Token) {
        $headers["Authorization"] = "token $Token"
    }
    return $headers
}

function Parse-GitHubUrl {
    param([string]$Url)

    $normalized = $Url -replace '\.git$', ''
    if ($normalized -match 'github\.com[/:]([^/]+)/([^/]+)$') {
        return @{ Owner = $Matches[1]; Repo = $Matches[2] }
    }
    return $null
}

function Get-GitHubDefaultBranch {
    param(
        [string]$Owner,
        [string]$Repo,
        [hashtable]$Headers
    )

    $url = "https://api.github.com/repos/$Owner/$Repo"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.default_branch
    }
    catch {
        Write-Warning "Could not resolve default branch for ${Owner}/${Repo}: $_"
        return "main"
    }
}

function Resolve-GitHubRef {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Ref,
        [hashtable]$Headers
    )

    # Try as a branch
    $url = "https://api.github.com/repos/$Owner/$Repo/git/ref/heads/$Ref"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.object.sha
    }
    catch { }

    # Try as a tag
    $url = "https://api.github.com/repos/$Owner/$Repo/git/ref/tags/$Ref"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        if ($response.object.type -eq "tag") {
            $tagUrl = $response.object.url
            $tagObj = Invoke-RestMethod -Uri $tagUrl -Headers $Headers -ErrorAction Stop
            return $tagObj.object.sha
        }
        return $response.object.sha
    }
    catch { }

    # Try as raw commit SHA
    $url = "https://api.github.com/repos/$Owner/$Repo/git/commits/$Ref"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.sha
    }
    catch {
        return $null
    }
}

function Get-GitHubTreeRecursive {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Sha,
        [hashtable]$Headers
    )

    $url = "https://api.github.com/repos/$Owner/$Repo/git/trees/${Sha}?recursive=1"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.tree
    }
    catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($status -eq 404) {
            Write-Warning "  Repository $Owner/$Repo or commit $($Sha.Substring(0,8)) not found (404)"
        }
        elseif ($status -eq 403) {
            Write-Warning "  GitHub API rate limit exceeded. Use -GitHubToken parameter."
        }
        else {
            Write-Warning "  GitHub API error for $Owner/$Repo at $($Sha.Substring(0,8)): $_"
        }
        return $null
    }
}

function Get-GitHubFileContentRaw {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Sha,
        [string]$FilePath,
        [hashtable]$Headers
    )

    $url = "https://raw.githubusercontent.com/$Owner/$Repo/$Sha/$FilePath"
    try {
        $content = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $content
    }
    catch {
        return $null
    }
}

# --- .gitmodules parser ---

function Parse-GitModulesContent {
    param([string]$Content)

    $submodules = @()
    $current = $null

    foreach ($line in ($Content -split "`n")) {
        $line = $line.Trim()
        if ($line -match '^\[submodule\s+"(.+)"\]$') {
            if ($current) { $submodules += $current }
            $current = @{ Name = $Matches[1]; Path = $null; Url = $null }
        }
        elseif ($current -and $line -match '^path\s*=\s*(.+)$') {
            $current.Path = $Matches[1].Trim()
        }
        elseif ($current -and $line -match '^url\s*=\s*(.+)$') {
            $current.Url = $Matches[1].Trim()
        }
    }
    if ($current) { $submodules += $current }

    return $submodules
}

function Normalize-SubmoduleRepoUrl {
    param([string]$Url)
    $n = $Url -replace '\.git$', ''
    return $n.ToLower().TrimEnd('/')
}

function Get-RepoNameFromUrl {
    param([string]$Url)
    $n = $Url -replace '\.git$', ''
    $parts = $n.Split('/')
    return $parts[-1]
}

function Resolve-SubmoduleUrl {
    param(
        [string]$ParentUrl,
        [string]$SubUrl
    )

    if ($SubUrl -match '^https?://' -or $SubUrl -match '^git@') {
        return $SubUrl
    }

    $baseUri = [System.Uri]::new($ParentUrl.TrimEnd('/') + "/")
    $resolved = [System.Uri]::new($baseUri, $SubUrl)
    return $resolved.AbsoluteUri
}

# --- Dependency graph builder ---

function Build-SubmoduleDependencyGraph {
    param(
        [string]$RootName,
        [string]$RootUrl,
        [string]$RootSha,
        [hashtable]$Headers,
        [string[]]$IgnoreRepos,
        [hashtable]$RootSubmodules
    )

    $repoEdges = @{}
    $repoUrls = @{}
    $allReferences = @{}

    $repoUrls[$RootName] = $RootUrl

    $queue = New-Object System.Collections.Queue
    $visited = @{}

    $rootChildren = @()

    if ($RootSubmodules) {
        foreach ($path in $RootSubmodules.Keys) {
            $sub = $RootSubmodules[$path]
            $subName = Get-RepoNameFromUrl -Url $sub.Url
            if ($subName -in $IgnoreRepos) { continue }

            $normalizedUrl = Normalize-SubmoduleRepoUrl -Url $sub.Url
            $rootChildren += $subName

            if (-not $repoUrls.ContainsKey($subName)) {
                $repoUrls[$subName] = $sub.Url
            }

            if (-not $allReferences.ContainsKey($normalizedUrl)) {
                $allReferences[$normalizedUrl] = @()
            }
            $allReferences[$normalizedUrl] += @{
                Sha          = $sub.Sha
                TreePath     = $path
                ReferencedBy = $RootName
                Name         = $subName
            }

            $visitKey = "$normalizedUrl|$($sub.Sha)"
            if (-not $visited.ContainsKey($visitKey)) {
                $visited[$visitKey] = $true
                $queue.Enqueue(@{
                    Url           = $sub.Url
                    NormalizedUrl = $normalizedUrl
                    Sha           = $sub.Sha
                    TreePath      = $path
                    Name          = $subName
                })
            }
        }
    }
    else {
        $ghRoot = Parse-GitHubUrl -Url $RootUrl
        if (-not $ghRoot) {
            Write-Error "Root URL is not a GitHub URL: $RootUrl"
            return $null
        }

        $gitmodulesContent = Get-GitHubFileContentRaw -Owner $ghRoot.Owner -Repo $ghRoot.Repo `
            -Sha $RootSha -FilePath ".gitmodules" -Headers $Headers
        if (-not $gitmodulesContent) {
            Write-Host "  No .gitmodules at root - nothing to check." -ForegroundColor Green
            return @{ Edges = $repoEdges; Urls = $repoUrls; References = $allReferences; ApiCalls = 1 }
        }

        $rootEntries = Parse-GitModulesContent -Content $gitmodulesContent

        $tree = Get-GitHubTreeRecursive -Owner $ghRoot.Owner -Repo $ghRoot.Repo -Sha $RootSha -Headers $Headers
        if (-not $tree) {
            Write-Warning "Could not fetch tree for root repo"
            return $null
        }

        $commitLookup = @{}
        foreach ($entry in $tree) {
            if ($entry.mode -eq "160000") {
                $commitLookup[$entry.path] = $entry.sha
            }
        }

        foreach ($sub in $rootEntries) {
            if (-not $sub.Path -or -not $sub.Url) { continue }

            $resolvedUrl = Resolve-SubmoduleUrl -ParentUrl $RootUrl -SubUrl $sub.Url
            $subName = Get-RepoNameFromUrl -Url $resolvedUrl
            if ($subName -in $IgnoreRepos) { continue }

            $sha = $commitLookup[$sub.Path]
            if (-not $sha) { continue }

            $normalizedUrl = Normalize-SubmoduleRepoUrl -Url $resolvedUrl
            $rootChildren += $subName

            if (-not $repoUrls.ContainsKey($subName)) {
                $repoUrls[$subName] = $resolvedUrl
            }

            if (-not $allReferences.ContainsKey($normalizedUrl)) {
                $allReferences[$normalizedUrl] = @()
            }
            $allReferences[$normalizedUrl] += @{
                Sha          = $sha
                TreePath     = $sub.Path
                ReferencedBy = $RootName
                Name         = $subName
            }

            $visitKey = "$normalizedUrl|$sha"
            if (-not $visited.ContainsKey($visitKey)) {
                $visited[$visitKey] = $true
                $queue.Enqueue(@{
                    Url           = $resolvedUrl
                    NormalizedUrl = $normalizedUrl
                    Sha           = $sha
                    TreePath      = $sub.Path
                    Name          = $subName
                })
            }
        }
    }

    $repoEdges[$RootName] = $rootChildren

    $apiCalls = 0
    $maxApiCalls = 500

    while ($queue.Count -gt 0 -and $apiCalls -lt $maxApiCalls) {
        $item = $queue.Dequeue()
        $ghInfo = Parse-GitHubUrl -Url $item.Url

        if (-not $ghInfo) {
            Write-Verbose "  Skipping non-GitHub URL: $($item.Url)"
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        Write-Progress -Activity "Building dependency graph" `
            -Status "Inspecting: $($item.Name) @ $($item.Sha.Substring(0,8))" `
            -CurrentOperation "API calls: $apiCalls | Queue: $($queue.Count)"

        $apiCalls++
        $subGitmodules = Get-GitHubFileContentRaw -Owner $ghInfo.Owner -Repo $ghInfo.Repo `
            -Sha $item.Sha -FilePath ".gitmodules" -Headers $Headers

        if (-not $subGitmodules) {
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        $subEntries = Parse-GitModulesContent -Content $subGitmodules
        if ($subEntries.Count -eq 0) {
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        $apiCalls++
        $tree = Get-GitHubTreeRecursive -Owner $ghInfo.Owner -Repo $ghInfo.Repo `
            -Sha $item.Sha -Headers $Headers

        if (-not $tree) {
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        $commitLookup = @{}
        foreach ($entry in $tree) {
            if ($entry.mode -eq "160000") {
                $commitLookup[$entry.path] = $entry.sha
            }
        }

        $children = @()
        foreach ($sub in $subEntries) {
            if (-not $sub.Path -or -not $sub.Url) { continue }

            $resolvedUrl = Resolve-SubmoduleUrl -ParentUrl $item.Url -SubUrl $sub.Url
            $subName = Get-RepoNameFromUrl -Url $resolvedUrl
            if ($subName -in $IgnoreRepos) { continue }

            $sha = $commitLookup[$sub.Path]
            if (-not $sha) { continue }

            $normalizedUrl = Normalize-SubmoduleRepoUrl -Url $resolvedUrl
            $treePath = "$($item.TreePath)/$($sub.Path)"
            $children += $subName

            if (-not $repoUrls.ContainsKey($subName)) {
                $repoUrls[$subName] = $resolvedUrl
            }

            if (-not $allReferences.ContainsKey($normalizedUrl)) {
                $allReferences[$normalizedUrl] = @()
            }
            $allReferences[$normalizedUrl] += @{
                Sha          = $sha
                TreePath     = $treePath
                ReferencedBy = $item.Name
                Name         = $subName
            }

            $visitKey = "$normalizedUrl|$sha"
            if (-not $visited.ContainsKey($visitKey)) {
                $visited[$visitKey] = $true
                $queue.Enqueue(@{
                    Url           = $resolvedUrl
                    NormalizedUrl = $normalizedUrl
                    Sha           = $sha
                    TreePath      = $treePath
                    Name          = $subName
                })
            }
        }

        $repoEdges[$item.Name] = $children
    }

    Write-Progress -Activity "Building dependency graph" -Completed

    if ($apiCalls -ge $maxApiCalls) {
        Write-Warning "Reached API call safety limit ($maxApiCalls). Results may be incomplete."
    }

    return @{
        Edges      = $repoEdges
        Urls       = $repoUrls
        References = $allReferences
        ApiCalls   = $apiCalls
    }
}

# --- Graph display ---

function Show-SubmoduleDependencyGraph {
    param(
        [string]$RootName,
        [hashtable]$Edges,
        [hashtable]$Urls,
        [hashtable]$References
    )

    $levels = @{}
    $levels[$RootName] = 0
    $levelQueue = New-Object System.Collections.Queue
    $levelQueue.Enqueue($RootName)

    while ($levelQueue.Count -gt 0) {
        $name = $levelQueue.Dequeue()
        $parentLevel = $levels[$name]

        if ($Edges.ContainsKey($name)) {
            foreach ($child in $Edges[$name]) {
                $currentLevel = 0
                if ($levels.ContainsKey($child)) { $currentLevel = $levels[$child] }
                if (($parentLevel + 1) -gt $currentLevel) {
                    $levels[$child] = $parentLevel + 1
                    $levelQueue.Enqueue($child)
                }
            }
        }
    }

    $sortedRepos = $levels.GetEnumerator() | Sort-Object {
        -$_.Value
    }, {
        $_.Key
    } | ForEach-Object { $_.Key }

    $repoDisplaySha = @{}
    foreach ($url in $References.Keys) {
        foreach ($ref in $References[$url]) {
            if (-not $repoDisplaySha.ContainsKey($ref.Name)) {
                $repoDisplaySha[$ref.Name] = $ref.Sha
            }
        }
    }

    $maxLevel = ($levels.Values | Measure-Object -Maximum).Maximum
    $maxNameLen = ($sortedRepos | ForEach-Object { $_.Length } | Measure-Object -Maximum).Maximum
    if ($maxNameLen -lt 10) { $maxNameLen = 10 }

    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "          DEPENDENCY GRAPH (update order)" -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host ""

    $header = "   {0,-4} {1,-$maxNameLen} {2,-10} {3}" -f "#", "REPOSITORY", "SHA", "LEVEL"
    Write-Host $header -ForegroundColor White
    Write-Host "   $("-" * 4) $("-" * $maxNameLen) $("-" * 10) $("-" * 8)" -ForegroundColor DarkGray

    $index = 1
    foreach ($repo in $sortedRepos) {
        $level = $levels[$repo]
        $sha = if ($repoDisplaySha.ContainsKey($repo)) { $repoDisplaySha[$repo].Substring(0, 8) } else { "--------" }

        $color = switch ($level) {
            0 { "Cyan" }
            1 { "White" }
            2 { "Gray" }
            default { "DarkGray" }
        }

        $levelBar = [string]::new([char]0x2588, $level) + [string]::new([char]0x2591, $maxLevel - $level)

        $line = "   {0,-4} {1,-$maxNameLen} {2,-10} {3} ({4})" -f "$index.", $repo, $sha, $levelBar, $level
        Write-Host $line -ForegroundColor $color
        $index++
    }

    Write-Host ""
    Write-Host "   Levels: 0 = root, $maxLevel = leaf (updated first)" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "-------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "   EDGES (repo -> dependencies)" -ForegroundColor Cyan
    Write-Host "-------------------------------------------------------" -ForegroundColor DarkGray

    $displayOrder = $levels.GetEnumerator() | Sort-Object { $_.Value }, { $_.Key } | ForEach-Object { $_.Key }
    foreach ($repo in $displayOrder) {
        if ($Edges.ContainsKey($repo) -and $Edges[$repo].Count -gt 0) {
            $children = ($Edges[$repo] | Sort-Object) -join ", "
            Write-Host "   $repo " -ForegroundColor White -NoNewline
            Write-Host "-> " -ForegroundColor DarkGray -NoNewline
            Write-Host $children -ForegroundColor Gray
        }
    }

    Write-Host ""
}

# --- Conflict display ---

function Show-SubmoduleConflicts {
    param(
        [array]$Conflicts
    )

    Write-Host "=======================================================" -ForegroundColor Red
    Write-Host "     SUBMODULE CONSISTENCY CONFLICTS" -ForegroundColor Red
    Write-Host "=======================================================" -ForegroundColor Red
    Write-Host ""

    foreach ($conflict in $Conflicts) {
        Write-Host "  $([char]0x2717) $($conflict.Name)" -ForegroundColor Yellow
        Write-Host "    URL: $($conflict.Url)" -ForegroundColor DarkGray

        $groups = $conflict.Refs | Group-Object { $_.Sha }
        foreach ($group in $groups) {
            $sha = $group.Name.Substring(0, 8)
            Write-Host "    SHA $sha referenced by:" -ForegroundColor White
            foreach ($ref in $group.Group) {
                Write-Host "      $([char]0x2502) $($ref.TreePath)" -ForegroundColor Gray -NoNewline
                Write-Host " (via $($ref.ReferencedBy))" -ForegroundColor DarkGray
            }
        }
        Write-Host ""
    }
}

# --- Main exported function ---

<#
.SYNOPSIS
Check submodule consistency for a repository (local or remote) without cloning.

.DESCRIPTION
Walks the submodule dependency tree using GitHub APIs and verifies that whenever
the same repository appears as a submodule in multiple places, all references
point to the same commit SHA. Builds and displays the full dependency graph.

Can operate in two modes:
  1. Remote-only: pass -RepoUrl (e.g. "https://github.com/Azure/azure-iot-sdk-c")
  2. Local: pass -Path to a local git checkout.

.PARAMETER RepoUrl
URL of a GitHub repository to check (remote-only mode).

.PARAMETER Path
Path to a local git repository root (local mode).

.PARAMETER Branch
Branch, tag, or commit to check. Defaults to HEAD (local) or default branch (remote).

.PARAMETER GitHubToken
Optional GitHub PAT for API rate limits. Also reads GITHUB_TOKEN or GH_TOKEN env vars.

.PARAMETER IgnoreRepos
List of repository names to ignore during traversal.

.PARAMETER ShowTree
Print the full dependency tree with levels and update order.

.OUTPUTS
Returns $true if consistent, $false if conflicts found.
#>
function Test-SubmoduleConsistency {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$RepoUrl,

        [Parameter(Mandatory = $false)]
        [string]$Path,

        [Parameter(Mandatory = $false)]
        [string]$Branch,

        [Parameter(Mandatory = $false)]
        [string]$GitHubToken,

        [Parameter(Mandatory = $false)]
        [string[]]$IgnoreRepos = @(),

        [switch]$ShowTree
    )

    if (-not $GitHubToken) {
        $GitHubToken = if ($env:GITHUB_TOKEN) { $env:GITHUB_TOKEN }
                       elseif ($env:GH_TOKEN) { $env:GH_TOKEN }
                       else { $null }
    }
    $headers = Get-SubmoduleCheckGitHubHeaders -Token $GitHubToken

    $rootName = $null
    $rootUrl = $null
    $rootSha = $null
    $rootSubmodules = $null

    if ($RepoUrl) {
        # --- Remote mode ---
        $rootUrl = $RepoUrl -replace '\.git$', ''
        $rootName = Get-RepoNameFromUrl -Url $rootUrl
        $ghRoot = Parse-GitHubUrl -Url $rootUrl

        if (-not $ghRoot) {
            Write-Error "Not a GitHub URL: $RepoUrl"
            return $false
        }

        if (-not $Branch) {
            $Branch = Get-GitHubDefaultBranch -Owner $ghRoot.Owner -Repo $ghRoot.Repo -Headers $headers
            Write-Verbose "Using default branch: $Branch"
        }

        $rootSha = Resolve-GitHubRef -Owner $ghRoot.Owner -Repo $ghRoot.Repo -Ref $Branch -Headers $headers
        if (-not $rootSha) {
            Write-Error "Could not resolve ref '$Branch' for $($ghRoot.Owner)/$($ghRoot.Repo)"
            return $false
        }
    }
    else {
        # --- Local mode ---
        if (-not $Path) { $Path = "." }
        $repoPath = Resolve-Path $Path -ErrorAction Stop
        Push-Location $repoPath

        try {
            if (-not $Branch) { $Branch = "HEAD" }
            $rootSha = git rev-parse $Branch 2>$null
            if (-not $rootSha) {
                Write-Error "Could not resolve ref '$Branch' in $repoPath"
                return $false
            }

            $rootName = Split-Path $repoPath -Leaf

            $remoteUrl = git config --get remote.origin.url 2>$null
            if ($remoteUrl) {
                $rootUrl = $remoteUrl -replace '\.git$', ''
            }

            $gitmodulesPath = Join-Path $repoPath ".gitmodules"
            if (-not (Test-Path $gitmodulesPath)) {
                Write-Host "No .gitmodules found - nothing to check." -ForegroundColor Green
                return $true
            }

            $gitmodulesContent = Get-Content $gitmodulesPath -Raw
            $localEntries = Parse-GitModulesContent -Content $gitmodulesContent

            $lsTreeR = git ls-tree -r $Branch
            $subCommits = @{}
            foreach ($entry in ($lsTreeR -split "`n")) {
                if ($entry -match '^160000\s+commit\s+([0-9a-f]+)\s+(.+)$') {
                    $subCommits[$Matches[2]] = $Matches[1]
                }
            }

            $rootSubmodules = @{}
            foreach ($sub in $localEntries) {
                if (-not $sub.Path -or -not $sub.Url) { continue }
                $sha = $subCommits[$sub.Path]
                if (-not $sha) { continue }

                $resolvedUrl = if ($rootUrl) {
                    Resolve-SubmoduleUrl -ParentUrl $rootUrl -SubUrl $sub.Url
                } else {
                    $sub.Url
                }

                $rootSubmodules[$sub.Path] = @{
                    Url = $resolvedUrl
                    Sha = $sha
                }
            }
        }
        finally {
            Pop-Location
        }
    }

    # Display header
    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "  Submodule Consistency Check" -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "  Repository : $rootName" -ForegroundColor White
    Write-Host "  Ref        : $Branch" -ForegroundColor White
    Write-Host "  Commit     : $($rootSha.Substring(0, 12))" -ForegroundColor White
    if ($rootUrl) {
        Write-Host "  URL        : $rootUrl" -ForegroundColor DarkGray
    }
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host ""

    # Build the dependency graph
    Write-Host "  Building dependency graph..." -ForegroundColor Gray
    $graph = Build-SubmoduleDependencyGraph `
        -RootName $rootName `
        -RootUrl $rootUrl `
        -RootSha $rootSha `
        -Headers $headers `
        -IgnoreRepos $IgnoreRepos `
        -RootSubmodules $rootSubmodules

    if (-not $graph) {
        Write-Error "Failed to build dependency graph."
        return $false
    }

    Write-Host "  GitHub API calls: $($graph.ApiCalls)" -ForegroundColor DarkGray
    Write-Host "  Unique repos discovered: $($graph.Edges.Count)" -ForegroundColor DarkGray
    $totalRefs = ($graph.References.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
    Write-Host "  Total submodule references: $totalRefs" -ForegroundColor DarkGray

    # Show dependency graph
    if ($ShowTree) {
        Show-SubmoduleDependencyGraph -RootName $rootName -Edges $graph.Edges `
            -Urls $graph.Urls -References $graph.References
    }

    # Check for conflicts
    $conflicts = @()
    foreach ($url in $graph.References.Keys) {
        $refs = $graph.References[$url]
        $distinctShas = $refs | ForEach-Object { $_.Sha } | Sort-Object -Unique
        if ($distinctShas.Count -gt 1) {
            $conflicts += @{
                Url  = $url
                Name = Get-RepoNameFromUrl -Url $url
                Refs = $refs
                Shas = $distinctShas
            }
        }
    }

    # Report results
    Write-Host ""
    if ($conflicts.Count -eq 0) {
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host "  $([char]0x2713) RESULT: ALL SUBMODULES CONSISTENT" -ForegroundColor Green
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host "  All shared dependencies point to the same commit." -ForegroundColor Green
        Write-Host ""
        return $true
    }
    else {
        Show-SubmoduleConflicts -Conflicts $conflicts

        Write-Host "-------------------------------------------------------" -ForegroundColor Red
        Write-Host "  RESULT: $($conflicts.Count) INCONSISTENC$(if ($conflicts.Count -eq 1) { 'Y' } else { 'IES' }) FOUND" -ForegroundColor Red
        Write-Host "-------------------------------------------------------" -ForegroundColor Red
        Write-Host "  Fix: ensure all references to the same repo use the same commit." -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
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


