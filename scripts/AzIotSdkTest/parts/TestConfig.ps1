
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
