<#
.SYNOPSIS
Drives Add-AzIotSharedEnrollmentGroups with `az` stubbed: a first run, a rerun with the returned CA,
certificate issuance, an X.509-only DPS and a mismatched CA.

.DESCRIPTION
Provisions nothing and needs no credentials. The stub keeps the DPS certificates and enrollment
groups the module writes, and checks the proof of possession against the uploaded CA.

.EXAMPLE
pwsh -NoProfile -File tests/Test-SharedEnrollmentGroups.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $RepoRoot 'scripts/AzIotSdkTest/AzIotSdkTest.psd1') -Force
$Module = Get-Module AzIotSdkTest
& $Module { function script:Start-Sleep { } }

function global:Read-StubPemCertificate([string]$Path) {
    $Base64 = ((Get-Content -Raw -Path $Path) -replace '-----[A-Z ]+-----', '') -replace '\s+', ''
    [System.Security.Cryptography.X509Certificates.X509Certificate2]::new([Convert]::FromBase64String($Base64))
}

function Reset-Stub {
    $global:Stub = @{
        Calls = New-Object System.Collections.Generic.List[object]
        Certificates = @{}
        Groups = @{}
        NextKey = 0
    }
}

function global:az {
    # Flattened as a native az receives them: an array argument is one argument per item.
    $Argv = @($args | %{ $_ } | %{ "$_" })
    $Joined = $Argv -join ' '
    function Opt([string]$Name) { $i = [array]::IndexOf($Argv, $Name); if ($i -ge 0) { $Argv[$i + 1] } }
    $Call = @{ Line = $Joined; Body = $null }
    $global:Stub.Calls.Add($Call)
    $global:LASTEXITCODE = 0
    switch -Regex ($Joined) {
        '^iot dps connection-string show' { return 'HostName=stubdps.azure-devices-provisioning.net;SharedAccessKeyName=provisioningserviceowner;SharedAccessKey=RkFLRQ==' }
        '^iot dps certificate list' {
            $Name = [regex]::Match((Opt '--query'), "name=='([^']+)'").Groups[1].Value
            return (ConvertTo-Json -Depth 5 -InputObject @(@($global:Stub.Certificates[$Name]) | ?{ $_ } | %{ @{ name = $_.name; properties = $_.properties } }))
        }
        '^iot dps certificate create' {
            $Certificate = Read-StubPemCertificate (Opt '--path')
            $global:Stub.Certificates[(Opt '--name')] = @{ name = (Opt '--name'); properties = @{ thumbprint = $Certificate.Thumbprint; isVerified = $false }; Certificate = $Certificate }
            return '{}'
        }
        '^iot dps certificate show' { return 'etag' }
        '^iot dps certificate generate-verification-code' { return '{"properties":{"verificationCode":"stub-code"}}' }
        '^iot dps certificate verify' {
            $Entry = $global:Stub.Certificates[(Opt '--name')]
            $Proof = Read-StubPemCertificate (Opt '--path')
            $Chain = [System.Security.Cryptography.X509Certificates.X509Chain]::new()
            $Chain.ChainPolicy.RevocationMode = 'NoCheck'
            $Chain.ChainPolicy.VerificationFlags = 'AllowUnknownCertificateAuthority'
            [void]$Chain.ChainPolicy.ExtraStore.Add($Entry.Certificate)
            if ($Proof.Subject -eq 'CN=stub-code' -and $Chain.Build($Proof) -and $Chain.ChainElements[1].Certificate.Thumbprint -eq $Entry.Certificate.Thumbprint) {
                $Entry.properties.isVerified = $true
                return '{}'
            }
            Write-Error -ErrorAction Continue 'ERROR: proof of possession rejected'
            $global:LASTEXITCODE = 1
            return
        }
        '^rest --method (GET|PUT) --url https://stubdps\.azure-devices-provisioning\.net/enrollmentGroups/([^?]+)\?' {
            $Id = [uri]::UnescapeDataString($Matches[2])
            if ($Matches[1] -eq 'GET') {
                if ($global:Stub.Groups.ContainsKey($Id)) { return ($global:Stub.Groups[$Id] | ConvertTo-Json -Depth 10) }
                Write-Error -ErrorAction Continue 'ERROR: Not Found({"errorCode":404201,"message":"Enrollment group not found."})'
                $global:LASTEXITCODE = 1
                return
            }
            $Body = Get-Content -Raw -Path (Opt '--body').Substring(1) | ConvertFrom-Json
            $Call.Body = $Body
            $Call.IfMatch = @($Argv | ?{ $_ -like 'If-Match=*' }) -join ''
            if ($Body.attestation.type -eq 'symmetricKey' -and -not $Body.attestation.symmetricKey) {
                $global:Stub.NextKey++
                $Body.attestation | Add-Member symmetricKey ([pscustomobject]@{ primaryKey = "key-$($global:Stub.NextKey)-p"; secondaryKey = "key-$($global:Stub.NextKey)-s" })
            }
            $global:Stub.Groups[$Id] = $Body
            return ($Body | ConvertTo-Json -Depth 10)
        }
    }
    Write-Error -ErrorAction Continue "unexpected az call: $Joined"
    $global:LASTEXITCODE = 1
}

$Problems = New-Object System.Collections.Generic.List[string]
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { $Problems.Add($Message) } }
function Find-Calls([string]$Pattern) { @($Stub.Calls | ?{ $_.Line -match $Pattern }) }
function Find-GroupPut([string]$Id) { @(Find-Calls "^rest --method PUT --url \S+/enrollmentGroups/$Id\?")[0] }

$Common = @{ ResourceGroup = 'StubRg'; DpsName = 'stubdps' }

# First run: a new CA, verified on the DPS and referenced by the X.509 group; both groups static to the hub.
Reset-Stub
$First = Add-AzIotSharedEnrollmentGroups @Common -X509EnrollmentGroupId e2e-shared-x509 -SymmetricKeyEnrollmentGroupId e2e-shared-sas -IotHubHostName stubhub.azure-devices.net
$Ca = $First.X509EnrollmentGroup.Certificate
$CaName = "e2e-shared-x509-ca-$($Ca.GetThumbprint().Substring(0, 8).ToLowerInvariant())"
Assert ($Ca.Certificate.Subject -like 'CN=azure-iot-sdk-e2e-shared-x509-ca-*' -and $null -ne $Ca.PrivateKey) "first: expected a new group CA with its key, got '$($Ca.Certificate.Subject)'."
Assert ([int]($Ca.Certificate.NotAfter - [DateTime]::Now).TotalDays -in 729, 730) "first: the CA must be valid for 730 days, not until $($Ca.Certificate.NotAfter)."
Assert ($Stub.Certificates[$CaName].properties.isVerified -and $Stub.Certificates[$CaName].properties.thumbprint -eq $Ca.GetThumbprint()) "first: DPS certificate '$CaName' must be the CA, verified."
$X509Put = Find-GroupPut 'e2e-shared-x509'
$SasPut = Find-GroupPut 'e2e-shared-sas'
Assert ($X509Put.Body.attestation.x509.caReferences.primary -eq $CaName -and $X509Put.Body.provisioningStatus -eq 'enabled') "first: the X.509 group must reference '$CaName': $($X509Put.Body | ConvertTo-Json -Compress -Depth 10)"
foreach ($Put in @($X509Put, $SasPut)) {
    Assert ($Put.Body.allocationPolicy -eq 'static' -and (@($Put.Body.iotHubs) -join ',') -eq 'stubhub.azure-devices.net') "first: $($Put.Body.enrollmentGroupId) must be static to the hub."
    Assert ($null -eq $Put.Body.namespaceName -and -not $Put.IfMatch) "first: $($Put.Body.enrollmentGroupId) must be created without an ADR policy or If-Match."
}
Assert ($First.SymmetricKeyEnrollmentGroup.Id -eq 'e2e-shared-sas' -and $First.SymmetricKeyEnrollmentGroup.PrimaryKey -eq 'key-1-p' -and $First.SymmetricKeyEnrollmentGroup.SecondaryKey -eq 'key-1-s') "first: symmetric-key group info: $($First.SymmetricKeyEnrollmentGroup | ConvertTo-Json -Compress)"

# Rerun with the returned CA: nothing new on the DPS, both groups replaced in place, keys kept.
$CaPem = $Ca.ToPem() + "`n" + $Ca.PrivateKey.ToPem()
$Stub.Calls.Clear()
$Second = Add-AzIotSharedEnrollmentGroups @Common -X509EnrollmentGroupId e2e-shared-x509 -SymmetricKeyEnrollmentGroupId e2e-shared-sas -IotHubHostName stubhub.azure-devices.net -GroupCaPem $CaPem
Assert ($Second.X509EnrollmentGroup.Certificate.GetThumbprint() -eq $Ca.GetThumbprint()) "rerun: the given CA must be kept."
Assert ((Find-Calls '^iot dps certificate (create|generate-verification-code|verify)').Count -eq 0) "rerun: a verified CA must not be uploaded or verified again."
Assert ((Find-GroupPut 'e2e-shared-x509').IfMatch -eq 'If-Match=*' -and (Find-GroupPut 'e2e-shared-sas').IfMatch -eq 'If-Match=*') "rerun: existing groups must be replaced with If-Match: *."
Assert ((Find-GroupPut 'e2e-shared-sas').Body.attestation.symmetricKey.primaryKey -eq 'key-1-p' -and $Second.SymmetricKeyEnrollmentGroup.PrimaryKey -eq 'key-1-p' -and $Second.SymmetricKeyEnrollmentGroup.SecondaryKey -eq 'key-1-s') "rerun: the symmetric keys must be kept."
Assert ((Find-GroupPut 'e2e-shared-x509').Body.attestation.x509.caReferences.primary -eq $CaName) "rerun: the X.509 group must still reference '$CaName'."

# Certificate issuance: both groups carry the ADR policy.
Reset-Stub
$Policy = & $Module { [AdrPolicyReference]::new('azure-adr-ns', 'default', 'azure-adr-policy') }
Add-AzIotSharedEnrollmentGroups @Common -X509EnrollmentGroupId e2e-shared-csr-x509 -SymmetricKeyEnrollmentGroupId e2e-shared-csr-sas -IotHubHostName stubhub.azure-devices.net -AdrPolicy $Policy | Out-Null
foreach ($Id in 'e2e-shared-csr-x509', 'e2e-shared-csr-sas') {
    $Body = (Find-GroupPut $Id).Body
    Assert ($Body.namespaceName -eq 'azure-adr-ns' -and $Body.certificateAuthorityName -eq 'default' -and $Body.certificatePolicyName -eq 'azure-adr-policy') "csr: $Id must reference the ADR policy: $($Body | ConvertTo-Json -Compress -Depth 10)"
}

# X.509 only, default allocation: no symmetric-key group and no hub pinned.
Reset-Stub
$Mqttv5 = Add-AzIotSharedEnrollmentGroups @Common -X509EnrollmentGroupId e2e-x509
$Body = (Find-GroupPut 'e2e-x509').Body
Assert ($null -eq $Mqttv5.SymmetricKeyEnrollmentGroup -and @($Stub.Groups.Keys).Count -eq 1) "x509-only: expected one group, got $(@($Stub.Groups.Keys) -join ',')."
Assert ($null -eq $Body.allocationPolicy -and $null -eq $Body.iotHubs) "x509-only: no hub must be pinned: $($Body | ConvertTo-Json -Compress -Depth 10)"

# A key that does not belong to the certificate fails before anything is called.
Reset-Stub
$OtherKey = & $Module { Export-Pkcs8PrivateKeyPem -Key (New-RsaPrivateKey) }
$Thrown = $null
try { Add-AzIotSharedEnrollmentGroups @Common -X509EnrollmentGroupId e2e-x509 -GroupCaPem ($Ca.ToPem() + "`n" + $OtherKey) | Out-Null } catch { $Thrown = $_.Exception.Message }
Assert ("$Thrown" -match 'does not belong' -and $Stub.Calls.Count -eq 0) "mismatched CA: expected a refusal before any call; got '$Thrown' after $($Stub.Calls.Count) call(s)."

# A DPS certificate of the expected name but another thumbprint is never replaced or referenced.
Reset-Stub
$Stub.Certificates[$CaName] = @{ name = $CaName; properties = @{ thumbprint = 'OTHER'; isVerified = $true } }
$Thrown = $null
try { Add-AzIotSharedEnrollmentGroups @Common -X509EnrollmentGroupId e2e-shared-x509 -GroupCaPem $CaPem | Out-Null } catch { $Thrown = $_.Exception.Message }
Assert ("$Thrown" -match 'different certificate' -and (Find-Calls '^(iot dps certificate (create|verify)|rest)').Count -eq 0) "certificate clash: expected a refusal before any change; got '$Thrown'."

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: shared enrollment groups."
