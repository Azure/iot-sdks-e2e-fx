
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
