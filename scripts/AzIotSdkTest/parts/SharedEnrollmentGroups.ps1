# <[Shared DPS enrollment groups]>

function Add-AzIotSharedEnrollmentGroups {
    <#
    .SYNOPSIS
    Creates the DPS enrollment groups that test runs share in a permanent test environment, or brings
    existing ones up to date.

    .DESCRIPTION
    On an existing DPS, creates or updates:

      * an X.509 enrollment group for devices whose certificates chain to a group CA. The CA is
        uploaded to the DPS and verified (proof of possession) as
        '<X509EnrollmentGroupId>-ca-<first 8 thumbprint characters>', and the group references it:
        an ADR-linked DPS rejects devices of a group whose CA is only embedded in the group;
      * with -SymmetricKeyEnrollmentGroupId, a symmetric-key enrollment group. An existing group
        keeps its keys.

    Both assign devices to -IotHubHostName when given, and reference -AdrPolicy when given, so
    their devices get certificates issued.

    The DPS never holds the CA's private key. Keep the returned CA and pass it back with -GroupCaPem
    on a rerun, which then changes nothing; without it a new CA is created and the X.509 group moves
    to it. Storing the CA and keys anywhere is up to the caller.

    .PARAMETER ResourceGroup
    Resource group of the DPS.
    .PARAMETER DpsName
    Name of the DPS.
    .PARAMETER X509EnrollmentGroupId
    Id of the X.509 enrollment group.
    .PARAMETER SymmetricKeyEnrollmentGroupId
    Id of the symmetric-key enrollment group. Omit it for MQTT v5 hubs, which take X.509 only.
    .PARAMETER IotHubHostName
    Hub the groups assign their devices to (static allocation). Omit it to use the DPS default
    allocation over its linked hubs.
    .PARAMETER AdrPolicy
    ADR certificate policy the groups' devices get certificates from, e.g. the AdrPolicy of
    New-AzIotTestEnvironment -EnableCertificateManagement.
    .PARAMETER GroupCaPem
    The group CA to keep: a PEM 'CERTIFICATE' and its PKCS#8 'PRIVATE KEY'.
    .PARAMETER CaValidityDays
    Validity of a new group CA. Default is 730.

    .OUTPUTS
    An object with X509EnrollmentGroup ([DpsX509EnrollmentGroupInfo], whose Certificate is the group
    CA with its key) and SymmetricKeyEnrollmentGroup ([DpsSymmetricKeyEnrollmentGroupInfo], or $null).

    .EXAMPLE
    $Groups = Add-AzIotSharedEnrollmentGroups -ResourceGroup <rg> -DpsName <dps> `
        -X509EnrollmentGroupId e2e-shared-x509 -SymmetricKeyEnrollmentGroupId e2e-shared-sas `
        -IotHubHostName <hub>.azure-devices.net
    $GroupCaPem = $Groups.X509EnrollmentGroup.Certificate.ToPem() + "`n" + $Groups.X509EnrollmentGroup.Certificate.PrivateKey.ToPem()
    #>
    param(
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Parameter(Mandatory = $true)][string]$DpsName,
        [Parameter(Mandatory = $true)][string]$X509EnrollmentGroupId,
        [string]$SymmetricKeyEnrollmentGroupId = $null,
        [string]$IotHubHostName = $null,
        [AdrPolicyReference]$AdrPolicy = $null,
        [string]$GroupCaPem = $null,
        [ValidateRange(1, 3650)][int]$CaValidityDays = 730
    )

    # Enrollment group ids are case-insensitive; one id would make the second group replace the first.
    if ($SymmetricKeyEnrollmentGroupId -eq $X509EnrollmentGroupId) {
        throw "The X.509 and symmetric-key enrollment groups need different ids, not '$X509EnrollmentGroupId'."
    }

    if ([string]::IsNullOrWhiteSpace($GroupCaPem)) {
        $CaKey = New-RsaPrivateKey
        $CaCertificate = New-Certificate -Subject "CN=azure-iot-sdk-$X509EnrollmentGroupId-ca-$([DateTime]::UtcNow.ToString('yyyyMMdd'))" `
            -Key $CaKey -IsCA $true -Days $CaValidityDays
        $GroupCa = [X509CertificateInfo]::new($CaKey, $CaCertificate)
    } else {
        $GroupCa = ConvertFrom-X509CertificateAndKeyPem -Pem $GroupCaPem
    }

    $DpsCertificateName = "$X509EnrollmentGroupId-ca-$($GroupCa.GetThumbprint().Substring(0, 8).ToLowerInvariant())"
    Add-VerifiedDpsCertificate -ResourceGroup $ResourceGroup -DpsName $DpsName -Name $DpsCertificateName `
        -Certificate $GroupCa.Certificate -PrivateKey $GroupCa.PrivateKey.ToNativeRsaKey()

    Set-SharedEnrollmentGroup -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentGroupId $X509EnrollmentGroupId `
        -IotHubHostName $IotHubHostName -AdrPolicy $AdrPolicy `
        -Attestation @{ type = "x509"; x509 = @{ caReferences = @{ primary = $DpsCertificateName } } } | Out-Null
    Write-Host "Enrollment group $X509EnrollmentGroupId references CA $($GroupCa.Certificate.Subject) ($DpsCertificateName), expiring $($GroupCa.Certificate.NotAfter.ToUniversalTime().ToString('u'))."

    $SymmetricKeyEnrollmentGroup = $null
    if (-not [string]::IsNullOrWhiteSpace($SymmetricKeyEnrollmentGroupId)) {
        $Group = Set-SharedEnrollmentGroup -ResourceGroup $ResourceGroup -DpsName $DpsName -EnrollmentGroupId $SymmetricKeyEnrollmentGroupId `
            -IotHubHostName $IotHubHostName -AdrPolicy $AdrPolicy -Attestation @{ type = "symmetricKey" }
        if ([string]::IsNullOrWhiteSpace($Group.attestation.symmetricKey.primaryKey)) {
            throw "Enrollment group $SymmetricKeyEnrollmentGroupId returned no primary key."
        }
        $SymmetricKeyEnrollmentGroup = [DpsSymmetricKeyEnrollmentGroupInfo]::new($SymmetricKeyEnrollmentGroupId,
            $Group.attestation.symmetricKey.primaryKey, $Group.attestation.symmetricKey.secondaryKey)
        Write-Host "Enrollment group $SymmetricKeyEnrollmentGroupId (symmetric key) is set."
    }

    return [pscustomobject]@{
        X509EnrollmentGroup = [DpsX509EnrollmentGroupInfo]::new($X509EnrollmentGroupId, $GroupCa)
        SymmetricKeyEnrollmentGroup = $SymmetricKeyEnrollmentGroup
    }
}

function Set-SharedEnrollmentGroup {
    <#
    .SYNOPSIS
    Creates or replaces an enabled enrollment group with -Attestation, keeping the symmetric keys of
    an existing one, and returns it.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Parameter(Mandatory = $true)][string]$DpsName,
        [Parameter(Mandatory = $true)][string]$EnrollmentGroupId,
        [Parameter(Mandatory = $true)][Hashtable]$Attestation,
        [string]$IotHubHostName = $null,
        [AdrPolicyReference]$AdrPolicy = $null
    )

    $Existing = Get-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollmentGroups" -EnrollmentId $EnrollmentGroupId

    # Without keys the DPS would issue new ones, and devices holding the old ones would fail.
    if ($Attestation.type -eq "symmetricKey" -and $null -ne $Existing -and $null -ne $Existing.attestation.symmetricKey) {
        $Attestation.symmetricKey = @{
            primaryKey = $Existing.attestation.symmetricKey.primaryKey
            secondaryKey = $Existing.attestation.symmetricKey.secondaryKey
        }
    }

    $Body = Add-AdrPolicyReference -AdrPolicy $AdrPolicy -Body @{
        enrollmentGroupId = $EnrollmentGroupId
        attestation = $Attestation
        provisioningStatus = "enabled"
    }
    if (-not [string]::IsNullOrWhiteSpace($IotHubHostName)) {
        $Body.allocationPolicy = "static"
        $Body.iotHubs = @($IotHubHostName)
    }

    return Set-DpsEnrollment -ResourceGroup $ResourceGroup -DpsName $DpsName -Collection "enrollmentGroups" `
        -EnrollmentId $EnrollmentGroupId -Body $Body -Replace:($null -ne $Existing)
}

function ConvertFrom-X509CertificateAndKeyPem {
    <#
    .SYNOPSIS
    Reads a PEM 'CERTIFICATE' and its PKCS#8 'PRIVATE KEY' into an [X509CertificateInfo].
    #>
    param([Parameter(Mandatory = $true)][string]$Pem)

    $CertificatePem = [regex]::Match($Pem, '-----BEGIN CERTIFICATE-----[\s\S]+?-----END CERTIFICATE-----')
    $KeyPem = [regex]::Match($Pem, '-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----')
    if (-not $CertificatePem.Success -or -not $KeyPem.Success) {
        throw "Expected a PEM 'CERTIFICATE' and its PKCS#8 'PRIVATE KEY'."
    }

    $Certificate = New-X509Certificate2FromPem -Pem $CertificatePem.Value
    $Key = New-RsaKeyFromPem -Pem $KeyPem.Value
    $CertificateModulus = [Convert]::ToBase64String([System.Security.Cryptography.X509Certificates.RSACertificateExtensions]::GetRSAPublicKey($Certificate).ExportParameters($false).Modulus)
    if ($CertificateModulus -ne [Convert]::ToBase64String($Key.ExportParameters($false).Modulus)) {
        throw "The PEM private key does not belong to certificate $($Certificate.Subject)."
    }

    return [X509CertificateInfo]::new($Key, $Certificate)
}
