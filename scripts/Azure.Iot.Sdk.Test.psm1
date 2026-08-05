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

# The azure-iot CLI extension version this repo provisions with.
#
# Provisioning needs the `az iot adr` command group, which ships only in the
# preview builds. 0.30.0 final dropped it, and because a final release outranks
# its own pre-releases, `--allow-preview` started resolving to 0.30.0 instead
# of 0.30.0b2 -- so the command group disappeared with no change on our side and
# every provisioning run began failing with:
#
#   ERROR: 'adr' is misspelled or not recognized by the system.
#
# Pinning is what makes this reproducible: `--allow-preview` selects whatever
# happens to be newest, which is not a version this repo ever tested against.
# TODO: drop the pin and install the stable extension once `adr` ships in one.
$script:AzureIotCliExtensionVersion = "0.30.0b2"

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
        az extension add --name azure-iot --version $script:AzureIotCliExtensionVersion --allow-preview --only-show-errors | Out-Null
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

class DpsInfo {
    [string]$ResourceGroup = $null
    [string]$DeviceFqdn = $null
    [string]$ServiceFqdn = $null
    [string]$ConnectionString = $null
    [string]$IdScope = $null
    [X509CertificateInfo[]]$RootCaCertificates = @()
    [DpsEnrollmentsSet]$Enrollments = [DpsEnrollmentsSet]::new()
    [string[]]$LinkedIotHubs = @()

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
        [string]$AzureAdrPolicyName,
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

        if ([string]::IsNullOrWhiteSpace($AzureAdrPolicyName) -and $UseAdrPolicy) {
            $AzureAdrPolicyName = $this.AzureAdrPolicyName
        }

        if ($null -eq $CertificateExpiration) {
            $DefaultCertificateExpiration = [TimeSpan]::FromDays(365)

            $CertificateExpiration = $DefaultCertificateExpiration
        }

        $GroupX509Enrollment = Add-DpsX509EnrollmentGroup -ResourceGroup $this.ResourceGroup -DpsName $this.GetName() -EnrollmentId $EnrollmentId -IssuerCertificate $IssuerCertificate -IssuerPrivateKey $IssuerPrivateKey -IotHubFqdn $IotHubFqdn -AdrPolicyName $AzureAdrPolicyName -CertificateExpiration $CertificateExpiration
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

    [string]$AzureAdrPolicyName = $null

    [hashtable]ToHashtable() {
        return [ordered]@{
            AzureResourceGroup = $this.AzureResourceGroup
            IotHub = ConvertTo-Hashtable -Object $this.IotHub
            Dps = ConvertTo-Hashtable -Object $this.Dps
            # TODO: add container registry
            AzureAdrPolicyName = $this.AzureAdrPolicyName
        }
    }

    static [TestEnvironmentInfo]FromHashtable([hashtable]$Hashtable) {
        $TestEnvironmentInfo = [TestEnvironmentInfo]::new()
        $TestEnvironmentInfo.AzureResourceGroup = $Hashtable.AzureResourceGroup
        $TestEnvironmentInfo.AzureAdrPolicyName = $Hashtable.AzureAdrPolicyName
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

function Add-DpsSymmetricKeyIndividualEnrollment {
    param(
        [string]$ResourceGroup = $null,
        [string]$DpsName = $null,
        [string]$EnrollmentId = $null,
        [string]$AdrPolicyName = $null
    )

    Write-Host "Creating Azure DPS symmetric-key individual enrollment ($EnrollmentId; $AdrPolicyName)."

    if ([string]::IsNullOrWhiteSpace($AdrPolicyName)) {
        $EnrollmentInfo = az iot dps enrollment create --dps-name $DpsName --resource-group $ResourceGroup --at symmetricKey --enrollment-id $EnrollmentId  | ConvertFrom-Json
    } else {
        $EnrollmentInfo = az iot dps enrollment create --dps-name $DpsName --resource-group $ResourceGroup --at symmetricKey --enrollment-id $EnrollmentId --credential-policy $AdrPolicyName | ConvertFrom-Json
    }

    Stop-OnError -Step "Create an Azure DPS symmetric-key individual enrollment ($EnrollmentId; $AdrPolicyName)"

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
        [string]$AdrPolicyName = $null,
        [timespan]$CertificateExpiration = $DefaultCertificateExpiration
    )

    Write-Host "Creating Azure DPS x509 individual enrollment ($EnrollmentId; $AdrPolicyName; $CertificatesDir; $PrivateKeysDir; $CertificateExpiration)."

    $DpsDevicePrivateKey = New-RsaPrivateKey
    $DpsDeviceCertificate = New-Certificate -Subject "CN=$EnrollmentId" -Key $DpsDevicePrivateKey -IssuerCert $null -IssuerKey $null -IsCA $false -Days $CertificateExpiration.TotalDays

    # az iot dps validates certificate files by name: only .pem and .cer are accepted.
    $DpsDeviceCertificatePath = New-TempFile -Extension "pem"
    Export-X509CertificateToPemFile -Cert $DpsDeviceCertificate -Path $DpsDeviceCertificatePath

    if ([string]::IsNullOrWhiteSpace($AdrPolicyName)) {
        az iot dps enrollment create --dps-name $DpsName --resource-group $ResourceGroup --at x509 --enrollment-id $EnrollmentId --cp $DpsDeviceCertificatePath | Out-Null
    } else {
        az iot dps enrollment create --dps-name $DpsName --resource-group $ResourceGroup --at x509 --enrollment-id $EnrollmentId --cp $DpsDeviceCertificatePath --credential-policy $AdrPolicyName | Out-Null
    }

    Stop-OnError -Step "Create an Azure DPS x509 individual enrollment ($EnrollmentId)"

    Remove-Item $DpsDeviceCertificatePath

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
        [string]$AdrPolicyName = $null
    )

    Write-Host "Creating Azure DPS symmetric-key enrollment group ($EnrollmentId; $AdrPolicyName)."

    if ([string]::IsNullOrWhiteSpace($AdrPolicyName)) {
        $EnrollmentInfo = az iot dps enrollment-group create --dps-name $DpsName --resource-group $ResourceGroup --enrollment-id $EnrollmentId | ConvertFrom-Json
    } else {
        $EnrollmentInfo = az iot dps enrollment-group create --dps-name $DpsName --resource-group $ResourceGroup --enrollment-id $EnrollmentId --credential-policy $AdrPolicyName | ConvertFrom-Json
    }

    Stop-OnError -Step "Create an Azure Device Provisioning symmetric-key enrollment group ($EnrollmentId; $AdrPolicyName)"

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
        [string]$AdrPolicyName = $null,
        [timespan]$CertificateExpiration = $DefaultCertificateExpiration
    )

    Write-Host "Creating Azure DPS x509 enrollment group ($EnrollmentId; $AdrPolicyName)."

    $ICA = Add-DpsCertificate -ResourceGroup $ResourceGroup -DpsName $DpsName -Subject $EnrollmentId -IssuerCert $IssuerCertificate -IssuerKey $IssuerPrivateKey -Expiration $CertificateExpiration

    # az iot dps validates certificate files by name: only .pem and .cer are accepted.
    $ICACertificatePath = New-TempFile -Extension "pem"
    $ICA.ExportToPemFile($ICACertificatePath)

    if ([string]::IsNullOrWhiteSpace($AdrPolicyName)) {
        az iot dps enrollment-group create --dps-name $DpsName --resource-group $ResourceGroup --enrollment-id $EnrollmentId --ap static --cp $ICACertificatePath --provisioning-status enabled --iot-hubs $IotHubFqdn  | Out-Null
    } else {
        az iot dps enrollment-group create --dps-name $DpsName --resource-group $ResourceGroup --enrollment-id $EnrollmentId --ap static --cp $ICACertificatePath --provisioning-status enabled --iot-hubs $IotHubFqdn --credential-policy $AdrPolicyName | Out-Null
    }

    Stop-OnError -Step "Create an Azure Device Provisioning x509 enrollment group ($EnrollmentId; $AdrPolicyName)"

    Remove-Item $ICACertificatePath

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

function Remove-LeftoverAzureResourceGroups {
    <#
    .SYNOPSIS
    Deletes resource groups created by this repository's pipelines that are older than a threshold.

    .DESCRIPTION
    Finds every resource group whose name starts with -Prefix (which defaults to the value returned
    by Get-AzureResourceGroupNamePrefix, i.e. only the resource groups created by this framework's
    pipelines) and deletes those whose 'CreatedOn' tag shows they were created more than
    -MinimumAgeHours hours ago. Resource groups created within the last -MinimumAgeHours hours are
    left untouched so that in-progress pipeline runs are never disturbed. Resource groups without a
    parseable 'CreatedOn' tag are skipped, because their age cannot be determined safely.

    Deletions are issued with '--no-wait'; this function returns after queuing them.

    .PARAMETER Prefix
    Resource group name prefix to match. Defaults to Get-AzureResourceGroupNamePrefix (this
    repository's prefix). Another repository that reuses this function should pass the prefix its
    own pipelines use, so that only its resource groups are considered for deletion.

    .PARAMETER MinimumAgeHours
    Minimum age, in hours, a resource group must have before it is eligible for deletion. Resource
    groups created this many hours ago or less are kept. Default is 3.

    .EXAMPLE
    PS> Remove-LeftoverAzureResourceGroups -MinimumAgeHours 3

    Deletes matching resource groups older than 3 hours.

    .EXAMPLE
    PS> Remove-LeftoverAzureResourceGroups -WhatIf

    Lists the resource groups that would be deleted without deleting them.
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Prefix = $(Get-AzureResourceGroupNamePrefix),
        [int]$MinimumAgeHours = 3
    )

    $Now = (Get-Date).ToUniversalTime()
    $Cutoff = $Now.AddHours(-$MinimumAgeHours)

    Write-Host "Cleanup run (UTC)     : $($Now.ToString('o'))"
    Write-Host "Resource group prefix : '$Prefix'"
    Write-Host "Minimum age to delete : $MinimumAgeHours hour(s) (delete when created at or before $($Cutoff.ToString('o')))"

    $RawJson = az group list --query "[].{name:name, createdOn:tags.CreatedOn, runUrl:tags.AzDevOpsRunUrl}" -o json --only-show-errors
    Stop-OnError -Step "List Azure resource groups" -Throw

    $Groups = @($RawJson | ConvertFrom-Json | Where-Object {
        $_.name -and $_.name.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)
    })

    Write-Host "Found $($Groups.Count) resource group(s) matching prefix '$Prefix'."

    $Deleted = [System.Collections.Generic.List[string]]::new()
    $Skipped = [System.Collections.Generic.List[string]]::new()
    $Failed  = [System.Collections.Generic.List[string]]::new()

    foreach ($Group in $Groups) {
        $Name = $Group.name
        $CreatedOnValue = $Group.createdOn

        if ($null -eq $CreatedOnValue -or [string]::IsNullOrWhiteSpace([string]$CreatedOnValue)) {
            Write-Host "SKIP   $Name : no 'CreatedOn' tag; age cannot be determined."
            $Skipped.Add($Name)
            continue
        }

        # ConvertFrom-Json parses the ISO-8601 'CreatedOn' tag (which always carries a UTC offset)
        # into a [datetime], so normalize whatever type we received back to a UTC instant.
        $CreatedOn = $null
        try {
            if ($CreatedOnValue -is [datetimeoffset]) {
                $CreatedOn = $CreatedOnValue.UtcDateTime
            } elseif ($CreatedOnValue -is [datetime]) {
                $CreatedOn = ([datetimeoffset]$CreatedOnValue).UtcDateTime
            } else {
                $CreatedOn = [datetimeoffset]::Parse(
                    [string]$CreatedOnValue,
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [System.Globalization.DateTimeStyles]::AssumeUniversal).UtcDateTime
            }
        } catch {
            Write-Host "SKIP   $Name : unparseable 'CreatedOn' tag value '$CreatedOnValue'."
            $Skipped.Add($Name)
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
    Write-Host "Skipped (too new / no tag) : $($Skipped.Count)"
    Write-Host "Failed to queue            : $($Failed.Count)"
    if ($Deleted.Count -gt 0) { Write-Host "Deleted: $($Deleted -join ', ')" }
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
    Specifies whether to enable certificate management in IoT Hub and DPS using Azure Device Registration (ADR). Default is false.

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

    # Required for some az iot commands, e.g. az iot adr ns create.
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

        $AzureResourceGroup = az group create --name "$ResourceGroup" --location "$AzureLocation" | ConvertFrom-json 

        Stop-OnError -Step "Create Azure resource group"

        Set-ResourceGroupTags -ResourceGroupId $AzureResourceGroup.id -Tags $ResourceGroupTags
        Stop-OnError -Step "Set Azure resource group tags"
    }

    $TestEnvInfo = [TestEnvironmentInfo]::new()

    # TODO: create Storage Account (required for IoT Hub file upload, if enabled) and add to $TestEnvInfo
    # Write-Host "Creating Azure Key Vault ($KeyVaultName)"
    # $AzureKeyVault = az keyvault create --name "$KeyVaultName" --resource-group "$ResourceGroup" --location "$AzureLocation" 2>$null | ConvertFrom-Json
    # Stop-OnError -Step "Create Azure Key Vault"

    if ($EnableCertificateManagement -eq $true) {
        $AzureIotHubAppId = "89d10474-74af-4874-99a7-c23c2f643083" # Azure IoT Hub application ID (same for all tenants)
        $AzureIotHubObjectId = "0aab4033-4ad9-4b0b-9934-542334eceffb" # Manually obtained...

        $ResourceGroupScope = "/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup"
        Write-Host "Creating Azure role assignment for certificate management (scope=$ResourceGroupScope)"
        if ($IsAzureAccountServicePrincipal) {
            az role assignment create --assignee-object-id $AzureIotHubObjectId --assignee-principal-type ServicePrincipal --role Contributor --scope "$ResourceGroupScope" --only-show-errors | Out-Null
        } else {
            az role assignment create --assignee $AzureIotHubAppId --role Contributor --scope "$ResourceGroupScope" --only-show-errors | Out-Null
        }
        Stop-OnError -Step "Create Azure role assignment for certificate management"

        $CertMgmtUserIdentity = "$($ResourceGroup)cmuid"
        Write-Host "Creating User-Assigned Managed Identity (UAMI) ($CertMgmtUserIdentity)"
        $AzureCertMgmtIdentity = az identity create --name "$CertMgmtUserIdentity" --resource-group "$ResourceGroup" --location "$AzureLocation" | ConvertFrom-Json
        Stop-OnError -Step "Create User-Assigned Managed Identity (UAMI)"

        $AzureAdrNamespaceName = "azure-adr-ns"
        $AzureAdrPolicyName = "azure-adr-policy"
        Write-Host "Creating ADR Namespace (ns=$AzureAdrNamespaceName; policy=$AzureAdrPolicyName)"
        $AzureAdrNamespace = az iot adr ns create --name "$AzureAdrNamespaceName" --enable-certificate-management --resource-group "$ResourceGroup" --location "$AzureLocation" --policy-name "$AzureAdrPolicyName" | ConvertFrom-Json
        Stop-OnError -Step "Create ADR Namespace"    

        # Azure Device Registry Contributor: namespaces/read,
        # namespaces/devices/*, namespaces/credentials/policies/read.
        $AdrContributorRoleId = "a5c3590a-3a1a-4cd4-9648-ea0a32b15137"
        # Azure Device Registry Onboarding: namespaces/write,
        # namespaces/credentials/*.
        $AdrOnboardingRoleId = "547f7f0a-69c0-4807-bd9e-0321dfb66a84"

        Write-Host "Assigning ADR custom role to UAMI ($AdrContributorRoleId)"
        az role assignment create --assignee "$($AzureCertMgmtIdentity.principalId)" --role "$AdrContributorRoleId" --scope "$($AzureAdrNamespace.id)" --only-show-errors | Out-Null
        Stop-OnError -Step "Assign ADR custom role 1 to UAMI"

        Write-Host "Assigning ADR custom role to UAMI ($AdrOnboardingRoleId)"
        az role assignment create --assignee "$($AzureCertMgmtIdentity.principalId)" --role "$AdrOnboardingRoleId" --scope "$($AzureAdrNamespace.id)" --only-show-errors | Out-Null
        Stop-OnError -Step "Assign ADR custom role 2 to UAMI"

        # IoT Hub and DPS validate this UAMI's DeviceRegistry permissions while
        # they are being created. The role assignments above were made seconds
        # ago and the enforcing providers may not observe them yet, so wait for
        # the assignments to be readable and then tolerate an access-denied
        # answer for a few attempts. Without this the create fails with
        # IH400913 "does not have the required DeviceRegistry permissions",
        # which is purely a propagation artifact.
        Wait-AzRoleAssignment `
            -PrincipalId "$($AzureCertMgmtIdentity.principalId)" `
            -Scope "$($AzureAdrNamespace.id)" `
            -RoleDefinitionIds @($AdrContributorRoleId, $AdrOnboardingRoleId)

        $AdrPermissionPropagationPattern = '400913|does not have the required DeviceRegistry permissions'

        Write-Host "Creating Azure IoT Hub ($IotHubName, with certificate management support)"
        $AzureIoTHub = Invoke-WithRetry -Step "Create Azure IoT Hub (with certificate management support)" `
            -RetryOnPattern $AdrPermissionPropagationPattern -Command {
            az iot hub create --name "$IotHubName" --resource-group "$ResourceGroup" --location "$AzureLocation" --sku GEN2 `
                --mi-user-assigned "$($AzureCertMgmtIdentity.id)" --ns-resource-id "$($AzureAdrNamespace.id)" --ns-identity-id "$($AzureCertMgmtIdentity.id)" | ConvertFrom-Json
        }

        Write-Host "Assigning Contributor role on Azure IoT for ADR principal"
        az role assignment create --assignee "$($AzureAdrNamespace.identity.principalId)" --role "Contributor" --scope "$($AzureIoTHub.id)" --only-show-errors | Out-Null
        Stop-OnError -Step "Assign Contributor role on Azure IoT for ADR principal"

        Write-Host "Assigning IoT Hub Registry Contributor role on Azure IoT for ADR principal"
        az role assignment create --assignee "$($AzureAdrNamespace.identity.principalId)" --role "IoT Hub Registry Contributor" --scope "$($AzureIoTHub.id)" --only-show-errors | Out-Null
        Stop-OnError -Step "Assign IoT Hub Registry Contributor role on Azure IoT for ADR principal"
        
        if ($NoDps -eq $false) {
            Write-Host "Creating Device Provisioning Service with ADR integration ($DpsName)"
            $AzureDps = Invoke-WithRetry -Step "Create Device Provisioning Service with ADR integration" `
                -RetryOnPattern $AdrPermissionPropagationPattern -Command {
                az iot dps create --name "$DpsName" --resource-group "$ResourceGroup" --location "$AzureLocation" `
                    --mi-user-assigned "$($AzureCertMgmtIdentity.id)" --ns-resource-id "$($AzureAdrNamespace.id)" --ns-identity-id "$($AzureCertMgmtIdentity.id)" --only-show-errors | ConvertFrom-Json
            }
        }
    } else {
        Write-Host "Creating Azure IoT Hub ($IotHubName)."
        $AzureIoTHub = az iot hub create --name "$IotHubName" --resource-group "$ResourceGroup" --location "$AzureLocation" --mintls "1.2" | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub"

        if ($NoDps -eq $false) {
            Write-Host "Creating Azure Device Provisioning Service ($DpsName)."
            $AzureDps = az iot dps create --name "$DpsName" --resource-group "$ResourceGroup" --location "$AzureLocation" | ConvertFrom-Json
            Stop-OnError -Step "Create Device Provisioning Service"
        }
    }

    if ($NoDps -eq $false) {    
        Write-Host "Linking Azure IoT Hub ($IotHubName) to Azure Device Provisioning service ($DpsName)"
        az iot dps linked-hub create --dps-name "$DpsName" --resource-group "$ResourceGroup" --hub-name "$IotHubName" | Out-Null
        Stop-OnError -Step "Link Azure IoT Hub to Azure Device Provisioning service"

        # Step was put here to optimize if blocks, since it's common down.
        Write-Host "Creating DPS Root Certificate"
        $DpsRootCertificate = Add-DpsCertificate -ResourceGroup $ResourceGroup -DpsName $DpsName
    }

    if ($EnableCertificateManagement -eq $true) {
        Write-Host "Syncing ADR credentials ($AzureAdrNamespaceName)."
        az iot adr ns credential sync --ns "$AzureAdrNamespaceName" --resource-group "$ResourceGroup" --only-show-errors | Out-Null
        Stop-OnError -Step "Sync ADR credentials"
    } else {
        $AzureAdrPolicyName = $null # Used below on enrollment creation.
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
            $EnrollmentInfo = Add-DpsSymmetricKeyIndividualEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicyName $AzureAdrPolicyName

            $TestEnvInfo.Dps.Enrollments.IndividualSymmetricKey += $EnrollmentInfo
        }

        for ($i = 0; $i -lt $DpsX509IndividualEnrollments; $i++) {
            $EnrollmentId = "$DpsX509EnrollmentIdPrefix-$i"
            $EnrollmentInfo = Add-DpsX509IndividualEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicyName $AzureAdrPolicyName

            $TestEnvInfo.Dps.Enrollments.IndividualX509 += $EnrollmentInfo
        }

        if ($DpsSymmKeyGroupEnrollmentDevices -gt 0) {
            $EnrollmentId = "$DpsSymmKeyEnrollmentIdPrefix-group"
            $SKEnrollmentGroupInfo = Add-DpsSymmetricKeyEnrollmentGroup -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicyName $AzureAdrPolicyName

            $TestEnvInfo.Dps.Enrollments.GroupSymmetricKey += $SKEnrollmentGroupInfo

            for ($i = 0; $i -lt $DpsSymmKeyGroupEnrollmentDevices; $i++) {
                $SKEnrollmentGroupInfo.AddIdentity("group-prov-sk-$i") | Out-Null
            }
        }

        if ($DpsX509GroupEnrollmentDevices -gt 0) {
            $EnrollmentId = "$DpsX509EnrollmentIdPrefix-group"
            $X509EnrollmentGroupInfo = Add-DpsX509EnrollmentGroup -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentId $EnrollmentId -AdrPolicyName $AzureAdrPolicyName -IssuerCertificate $DpsRootCertificate.ToNativeX509Certificate2() -IssuerPrivateKey $DpsRootCertificate.PrivateKey.ToNativeRsaKey() -IotHubFqdn $IotHubFqdn

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

        if ($EnableCertificateManagement -eq $true) {
            Write-Host "Updating Azure IoT Hub file upload settings (certificate management)"
            az iot hub update --name "$IotHubName" --resource-group "$ResourceGroup" --fcs "$AzureStorageConnectionString" --fc $AzureStorageContainerName --fileupload-sas-ttl 1 --ns-identity-id "$($AzureAdrNamespace.identity.principalId)" | Out-Null
            Stop-OnError -Step "Updating Azure IoT Hub file upload settings (certificate management)"
        } else {    
            Write-Host "Updating Azure IoT Hub file upload settings"
            az iot hub update --name "$IotHubName" --resource-group "$ResourceGroup" --fcs "$AzureStorageConnectionString" --fc $AzureStorageContainerName --fileupload-sas-ttl 1 | Out-Null
            Stop-OnError -Step "Updating Azure IoT Hub file upload settings"
        }
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
    $TestEnvInfo.AzureAdrPolicyName = $AzureAdrPolicyName

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
        $AzureDps.properties.iotHubs | %{ $TestEnvInfo.Dps.LinkedIotHubs += $_.name }

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

    # Required for some az iot commands, e.g. az iot adr ns create.
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

    if ([string]::IsNullOrWhiteSpace($IotHubName)) {
        if ($AzureDps.properties.iotHubs.Count -eq 0) {
            throw "Device Provisioning Service ($DpsName) does not have linked IoT hubs"
        }

        $IotHubName = $($AzureDps.properties.iotHubs[0].name.Split('.')[0])
    } else {
        $DpsLinkedIotHub = $AzureDps.properties.iotHubs | ?{$_.name -imatch "$IotHubName" }

        if ($null -eq $DpsLinkedIotHub) {
            throw "Iot Hub $IotHubName is not linked to $DpsName"
        }
    }

    $AzureIoTHub = az iot hub show --resource-group "$ResourceGroup" --name "$IotHubName" | ConvertFrom-Json

    # Gathering Test Environment settings.
    $TestEnvInfo.AzureResourceGroup = $AzureResourceGroup.name
    $TestEnvInfo.Dps.ResourceGroup = $AzureResourceGroup.name

    if ($null -ne $AzureIoTHub.properties.deviceRegistry.namespaceResourceId) {
        $AzureAdrNamespaceName = $AzureIoTHub.properties.deviceRegistry.namespaceResourceId.split("/")[8]
        $AzureAdrPolicy = az iot adr ns policy list --resource-group "$ResourceGroup" --ns "$AzureAdrNamespaceName" | ConvertFrom-Json
        $TestEnvInfo.AzureAdrPolicyName = $AzureAdrPolicy.name
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
    $AzureDps.properties.iotHubs | %{ $TestEnvInfo.Dps.LinkedIotHubs += $_.name }

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
            "`$env:ADR_CERT_MGMT_POLICY_NAME = `"$($TestEnvInfo.AzureAdrPolicyName)`""
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
            "export ADR_CERT_MGMT_POLICY_NAME=`"$($TestEnvInfo.AzureAdrPolicyName)`""
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
            "`$env:ADR_CERT_MGMT_POLICY_NAME = `"$($TestEnvInfo.AzureAdrPolicyName)`""
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
            "export ADR_CERT_MGMT_POLICY_NAME=`"$($TestEnvInfo.AzureAdrPolicyName)`""
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

            "`$env:ADR_CERT_MGMT_POLICY_NAME = `"$($TestEnvInfo.AzureAdrPolicyName)`""

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

            "export ADR_CERT_MGMT_POLICY_NAME=`"$($TestEnvInfo.AzureAdrPolicyName)`""

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


