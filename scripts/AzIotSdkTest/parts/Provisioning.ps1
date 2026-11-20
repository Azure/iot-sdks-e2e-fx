

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
    Specifies whether to enable file upload in IoT Hub, file upload notifications included. Default is false.
    .PARAMETER NoDps
    Specifies whether to skip creating a Device Provisioning Service. Default is false.
    .PARAMETER EnableCertificateManagement
    Specifies whether to enable certificate management for IoT Hub and DPS using Azure Device Registry (ADR). Default is false.
    Creates an ADR namespace, links the IoT Hub and DPS to it, and creates the certificate authority chain devices are issued certificates from. Requires a DPS, so it cannot be combined with -NoDps.
    .PARAMETER DisableLocalAuth
    Creates the IoT Hub with local (shared access policy) authentication disabled, so its service APIs accept only Microsoft Entra ID. Default is false.
    Device and module SAS and X.509 keep working. The signed-in principal is granted IoT Hub Data Contributor on the hub, the DPS gets a system-assigned identity and links to the hub with it, and hub data-plane calls use '--auth-type login'. The IoT Hub connection string stays in the output for its HostName only. The built-in Event Hub-compatible endpoint accepts only shared access keys, which the hub then refuses; use -RouteTelemetryToEventHub to read device telemetry.
    .PARAMETER RouteTelemetryToEventHub
    Routes device telemetry to an Event Hub of its own, read with Microsoft Entra ID only; see Add-AzIotEventHubTelemetryRoute. The signed-in principal can read it. Without -DisableLocalAuth, telemetry is also still routed to the built-in endpoint. Default is false.
    .PARAMETER TelemetryEventHubConsumerGroups
    Consumer groups to create on that Event Hub besides $Default, e.g. one per parallel test job.
    .PARAMETER IotHubUnits
    Number of IoT Hub S1 units. Default is 1. A permanent environment shared by parallel runs may need more.
    .PARAMETER DataPlaneServicePrincipalIds
    Object ids of service principals that use this environment with Microsoft Entra ID besides the signed-in one, e.g. the CI service connections of a permanent environment. They are granted IoT Hub Data Contributor on the hub and, with -RouteTelemetryToEventHub, Azure Event Hubs Data Receiver on the telemetry Event Hub.
    .PARAMETER Permanent
    Marks the environment as kept between runs: its resource group is tagged 'AzIotSdkTestPermanent=true', which Remove-LeftoverAzureResourceGroups never deletes. Requires a -ResourceGroup whose name does not start with Get-AzureResourceGroupNamePrefix. The resources are still created by this call; to rebuild them, delete the group or use another name.

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
        [switch]$DisableLocalAuth,
        [switch]$RouteTelemetryToEventHub,
        [string[]]$TelemetryEventHubConsumerGroups = @(),
        [ValidateRange(1, 200)][int]$IotHubUnits = 1,
        [string[]]$DataPlaneServicePrincipalIds = @(),
        [switch]$Permanent,
        [switch]$AddContainerRegistry
    )

    # Argument checks come before anything that touches Azure, so a bad invocation cannot leave a
    # resource group behind.
    if ($EnableCertificateManagement -eq $true -and $NoDps -eq $true) {
        throw "Certificate management requires a Device Provisioning Service; -NoDps and -EnableCertificateManagement are mutually exclusive."
    }
    if ($TelemetryEventHubConsumerGroups.Count -gt 0 -and -not $RouteTelemetryToEventHub) {
        throw "-TelemetryEventHubConsumerGroups requires -RouteTelemetryToEventHub."
    }

    $IotHubFqdn = "$($IotHubName).$($IotHubDomainName)"
    $DisableLocalAuthArgs = @(if ($DisableLocalAuth) { '--disable-local-auth', 'true' })
    # A hub without local auth takes only Entra ID on its data plane.
    $IotHubAuthArgs = @(if ($DisableLocalAuth) { '--auth-type', 'login' })

    $ResourceGroupContext = Initialize-AzIotTestResourceGroup -AzureLocation $AzureLocation -AzureSubscriptionId $AzureSubscriptionId `
        -ResourceGroup $ResourceGroup -ResourceGroupTags $ResourceGroupTags -Permanent:$Permanent
    $AzureAccount = $ResourceGroupContext.AzureAccount
    $AzureSubscriptionId = $ResourceGroupContext.SubscriptionId

    $TestEnvInfo = [TestEnvironmentInfo]::new()
    $AzureStorageContainerName = "iothubuploads"

    # TODO: create Storage Account (required for IoT Hub file upload, if enabled) and add to $TestEnvInfo
    # Write-Host "Creating Azure Key Vault ($KeyVaultName)"
    # $AzureKeyVault = az keyvault create --name "$KeyVaultName" --resource-group "$ResourceGroup" --location "$AzureLocation" 2>$null | ConvertFrom-Json
    # Stop-OnError -Step "Create Azure Key Vault"

    # Certificate management provisions the same three resources as the reference E2E harness for
    # this feature does, in the same shape: a plain S1 hub and a plain DPS, each with its own
    # system-assigned identity, and an ADR namespace they are both attached to afterwards through the
    # namespace's own endpoints. Nothing is pointed at anything else as it is created, which is what
    # the retired public-preview model did.
    if ($EnableCertificateManagement -eq $true) {

        # Created through ARM so it comes up with a system-assigned identity, which is the shape ADR
        # links. S1, not GEN2: a GEN2 hub carries the namespace in its own properties, which is the
        # retired model.
        $IotHubProperties = @{ disableLocalAuth = [bool]$DisableLocalAuth; minTlsVersion = "1.2" }

        # File upload is set here, at creation, because nothing can set it once ADR links the hub:
        # the link puts properties.deviceRegistry on the hub, and 'az iot hub update' then refuses
        # any non-GEN2 hub ("ADR properties are only supported for Generation2 IoT Hub SKUs").
        if ($EnableFileUpload -eq $true) {
            $AzureStorageConnectionString = New-FileUploadStorage -ResourceGroup $ResourceGroup -Location $AzureLocation `
                -StorageAccountName $StorageAccountName -ContainerName $AzureStorageContainerName
            $IotHubProperties["storageEndpoints"] = @{ '$default' = @{
                connectionString = $AzureStorageConnectionString
                containerName = $AzureStorageContainerName
                sasTtlAsIso8601 = "PT1H"
            } }
            $IotHubProperties["enableFileUploadNotifications"] = $true
        }

        Write-Host "Creating Azure IoT Hub ($IotHubName, with certificate management support)."
        $IotHubUrl = "https://management.azure.com/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Devices/IotHubs/$($IotHubName)?api-version=$($script:IotHubApiVersion)"
        $AzureIoTHub = New-AzArmResource -Url $IotHubUrl -Step "IoT Hub ($IotHubName)" -Body @{
            location = $AzureLocation
            sku = @{ name = "S1"; capacity = $IotHubUnits }
            identity = @{ type = "SystemAssigned" }
            properties = $IotHubProperties
        }
    } else {
        Write-Host "Creating Azure IoT Hub ($IotHubName)."
        $AzureIoTHub = Invoke-WithRetry -Step "Create Azure IoT Hub" -RetryOnPattern $script:IotTransientPattern -MaxAttempts 3 -Command {
            param($Attempt)
            if ($Attempt -gt 1) {
                $Existing = Resolve-AzIotResourceAfterFailedCreate -Type hub -Name $IotHubName -ResourceGroup $ResourceGroup
                if ($null -ne $Existing) { return $Existing }
            }
            az iot hub create --name "$IotHubName" --resource-group "$ResourceGroup" --location "$AzureLocation" --unit $IotHubUnits --mintls "1.2" @DisableLocalAuthArgs --only-show-errors | ConvertFrom-Json
        }
    }

    if ($DisableLocalAuth -eq $true) {
        Grant-IotHubDataContributorToSignedInPrincipal -AzureAccount $AzureAccount -IotHubId $AzureIoTHub.id -IotHubName $IotHubName -ResourceGroup $ResourceGroup
    }
    Grant-IotHubDataContributorToServicePrincipals -IotHubId $AzureIoTHub.id -ServicePrincipalIds $DataPlaneServicePrincipalIds

    if ($NoDps -eq $false) {
        if ($EnableCertificateManagement -eq $true -or $DisableLocalAuth -eq $true) {
            # Created through ARM rather than 'az iot dps create' so it comes up WITH a system-assigned
            # identity, which is what authenticates it to the ADR namespace, or to a hub without local
            # auth. The identity cannot be added afterwards: DPS rejects a managed-identity PATCH with
            # IH400158. Confined to these cases so ordinary provisioning keeps the CLI create and does
            # not take a dependency on a preview api-version it has no use for.
            Write-Host "Creating Azure Device Provisioning Service ($DpsName, with a system-assigned identity)."
            $DpsUrl = "$(Get-DpsArmHost -Location $AzureLocation)/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Devices/provisioningServices/$($DpsName)?api-version=$($script:DpsControlPlaneApiVersion)"
            $AzureDps = New-AzIotDpsWithSystemIdentity -Url $DpsUrl -DpsName $DpsName -Location $AzureLocation
        } else {
            Write-Host "Creating Azure Device Provisioning Service ($DpsName)."
            $AzureDps = Invoke-WithRetry -Step "Create Device Provisioning Service" -RetryOnPattern $script:IotTransientPattern -MaxAttempts 3 -Command {
                param($Attempt)
                if ($Attempt -gt 1) {
                    $Existing = Resolve-AzIotResourceAfterFailedCreate -Type dps -Name $DpsName -ResourceGroup $ResourceGroup
                    if ($null -ne $Existing) { return $Existing }
                }
                az iot dps create --name "$DpsName" --resource-group "$ResourceGroup" --location "$AzureLocation" --only-show-errors | ConvertFrom-Json
            }
        }
    }

    if ($EnableCertificateManagement -eq $true) {
        $AzureAdrPolicy = Connect-AzIotHubAndDpsToAdr -SubscriptionId $AzureSubscriptionId -ResourceGroup $ResourceGroup `
            -Location $AzureLocation -IotHub $AzureIoTHub -Dps $AzureDps
    } else {
        $AzureAdrPolicy = [AdrPolicyReference]::new() # Incomplete: no policy is referenced below.
    }

    if ($NoDps -eq $false) {
        # A DPS linked to an ADR namespace has ADR choosing its provisioning targets, and its own
        # linked-hub list is read-only from then on -- adding to it fails with IH409313.
        if ($EnableCertificateManagement -eq $false -and $DisableLocalAuth -eq $true) {
            # Without local auth the hub rejects the key a default link stores, so the DPS registers
            # devices as its own identity instead.
            Write-Host "Linking Azure IoT Hub ($IotHubName) to Azure Device Provisioning service ($DpsName) with the DPS identity"
            az role assignment create --assignee-object-id $AzureDps.identity.principalId --assignee-principal-type ServicePrincipal --role $script:IotHubDataContributorRoleId --scope $AzureIoTHub.id --only-show-errors | Out-Null
            Stop-OnError -Step "Assign IoT Hub Data Contributor on $IotHubName to the DPS identity"
            Wait-AzRoleAssignment -PrincipalId "$($AzureDps.identity.principalId)" -Scope "$($AzureIoTHub.id)" -RoleDefinitionIds @($script:IotHubDataContributorRoleId)
            # Through ARM: 'az iot dps linked-hub create --authentication-type' needs azure-iot 0.31.0b1+,
            # newer than the pinned extension (see Common.ps1). DPS has no PATCH for this, so the
            # create body is PUT again with the link.
            Invoke-WithRetry -Step "Link Azure IoT Hub to Azure Device Provisioning service" -RetryOnPattern "$($script:ArmTransientPattern)|$($script:DataPlaneAccessDeniedPattern)" -Command {
                Invoke-AzRest -Method PUT -Url $DpsUrl -Body @{
                    location = $AzureLocation
                    sku = @{ name = "S1"; capacity = 1 }
                    identity = @{ type = "SystemAssigned" }
                    properties = @{
                        iotHubs = @(@{
                            hostName = $AzureIoTHub.properties.hostName
                            location = $AzureLocation
                            authenticationType = "SystemAssigned"
                            applyAllocationPolicy = $true
                            allocationWeight = 1
                        })
                    }
                } | Out-Null
                Wait-AzProvisioningState -Url $DpsUrl -Step "Device Provisioning Service ($DpsName) link to $IotHubName"
            } | Out-Null
            $LinkedHub = @((Invoke-AzRest -Url $DpsUrl).properties.iotHubs) | Where-Object { $_.authenticationType -eq "SystemAssigned" }
            if ($null -eq $LinkedHub) {
                throw "Device Provisioning Service $DpsName does not list $IotHubName as linked with its identity."
            }
        } elseif ($EnableCertificateManagement -eq $false) {
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
        $IotHubDeviceInfo = az iot hub device-identity create --resource-group $ResourceGroup --hub-name $IotHubName --device-id $IotHubDeviceId @IotHubAuthArgs | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub symmetric-key device ($IotHubDeviceId)"
        $PrimaryConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $IotHubDeviceId --kt primary @IotHubAuthArgs | ConvertFrom-Json
        Stop-OnError -Step "Get Azure IoT Hub device primary connection-string ($IotHubDeviceId)"
        $SecondaryConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $IotHubDeviceId --kt secondary @IotHubAuthArgs | ConvertFrom-Json
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
        $IotHubDeviceInfo = az iot hub device-identity create --resource-group $ResourceGroup --hub-name $IotHubName --device-id $IotHubDeviceId @IotHubAuthArgs `
            --am x509_thumbprint --ptp $IotHubDevicePrimaryCertificate.Thumbprint --stp $IotHubDeviceSecondaryCertificate.Thumbprint | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub x509 thumbprint device ($IotHubDeviceId)"

        $ConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $IotHubDeviceId @IotHubAuthArgs | ConvertFrom-Json
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
    if ($EnableFileUpload -eq $true -and $EnableCertificateManagement -eq $true) {
        # Set when the hub was created. Read back after the ADR link, so a link that dropped it fails
        # here rather than as a silent file-upload e2e failure.
        Write-Host "Checking Azure IoT Hub file upload settings"
        $AzureIoTHubAfterLink = Invoke-AzRest -Url $IotHubUrl
        $DefaultStorage = $AzureIoTHubAfterLink.properties.storageEndpoints.'$default'
        # The account name, not the whole connection string: the hub returns the key masked.
        $LinkedStorageAccount = if ("$($DefaultStorage.connectionString)" -match '(?:^|;)AccountName=([^;]+)') { $Matches[1] } else { $null }
        if ($LinkedStorageAccount -ne $StorageAccountName -or
            $DefaultStorage.containerName -ne $AzureStorageContainerName -or
            $DefaultStorage.sasTtlAsIso8601 -ne "PT1H" -or
            $AzureIoTHubAfterLink.properties.enableFileUploadNotifications -ne $true) {
            throw "IoT Hub ($IotHubName) lost its file upload settings after the ADR link (account '$LinkedStorageAccount', container '$($DefaultStorage.containerName)', SAS TTL '$($DefaultStorage.sasTtlAsIso8601)', notifications '$($AzureIoTHubAfterLink.properties.enableFileUploadNotifications)')."
        }
    } elseif ($EnableFileUpload -eq $true) {
        $AzureStorageConnectionString = New-FileUploadStorage -ResourceGroup $ResourceGroup -Location $AzureLocation `
            -StorageAccountName $StorageAccountName -ContainerName $AzureStorageContainerName

        Write-Host "Updating Azure IoT Hub file upload settings"
        # Throttled (429) while other runs create hubs in the same subscription, or failing server-side
        # with "(IotHubUpdateFailed) An internal error occurred"; retry with backoff.
        Invoke-WithRetry -Step "Updating Azure IoT Hub file upload settings" -RetryOnPattern "$($script:ArmTransientPattern)|IotHubUpdateFailed\) An internal error" -Command {
            az iot hub update --name "$IotHubName" --resource-group "$ResourceGroup" --fcs "$AzureStorageConnectionString" --fc $AzureStorageContainerName --fileupload-sas-ttl 1 --fileupload-notifications true --only-show-errors | Out-Null
        } | Out-Null
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

    if ($RouteTelemetryToEventHub) {
        $TestEnvInfo.IotHub.TelemetryEventHub = Add-AzIotEventHubTelemetryRoute -ResourceGroup $ResourceGroup -IotHubName $IotHubName `
            -Location $AzureLocation -ConsumerGroups $TelemetryEventHubConsumerGroups -ReaderServicePrincipalIds $DataPlaneServicePrincipalIds `
            -KeepBuiltInEndpointRoute:(-not $DisableLocalAuth)
    }

    # Gathering Test Environment settings.
    $TestEnvInfo.AzureResourceGroup = $ResourceGroup
    $TestEnvInfo.Dps.ResourceGroup = $ResourceGroup
    $TestEnvInfo.AdrPolicy = $AzureAdrPolicy
    $TestEnvInfo.Dps.AdrPolicy = $AzureAdrPolicy
    $TestEnvInfo.IotHub.LocalAuthDisabled = [bool]$DisableLocalAuth

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
        Set-TestEnvironmentDpsInfo -DpsInfo $TestEnvInfo.Dps -Dps $AzureDps -ResourceGroup $ResourceGroup -DpsName $DpsName -LinkedIotHubFqdn $IotHubFqdn
        $TestEnvInfo.Dps.RootCaCertificates += $DpsRootCertificate
    }

    return $TestEnvInfo
}

function Initialize-AzIotTestResourceGroup {
    <#
    .SYNOPSIS
    Signs in to Azure if needed, selects the subscription, installs the azure-iot CLI extension, and
    creates the resource group with its tags, or updates the tags of an existing one.

    .PARAMETER ResourceGroupTags
    Tags to apply. CreatedBy/CreatedOn (or UpdatedBy/UpdatedOn) and AzDevOpsRunUrl are added to it.
    .PARAMETER Permanent
    Tags the group 'AzIotSdkTestPermanent=true', which Remove-LeftoverAzureResourceGroups never
    deletes, and refuses a name starting with Get-AzureResourceGroupNamePrefix.

    .OUTPUTS
    An object with AzureAccount ('az account show') and SubscriptionId.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$AzureLocation,
        [string]$AzureSubscriptionId = $null,
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Hashtable]$ResourceGroupTags = $null,
        [switch]$Permanent
    )

    $CleanupPrefix = Get-AzureResourceGroupNamePrefix
    if ($Permanent -and $ResourceGroup.StartsWith($CleanupPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "A permanent environment needs a resource group name that does not start with '$CleanupPrefix', the prefix of the groups the leftover-resource cleanup deletes; pass -ResourceGroup."
    }

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

    # Add default Azure resource group tags 
    if ($ResourceGroupTags -eq $null) {
        $ResourceGroupTags = @{}
    }

    $AzureDevOpsRunUrl = Get-AzureDevOpsRunUrl
    if ($null -ne $AzureDevOpsRunUrl) {
        $ResourceGroupTags.Add("AzDevOpsRunUrl", $AzureDevOpsRunUrl)
    }

    if ($Permanent) {
        $ResourceGroupTags[$script:PermanentTagName] = "true"
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

    return [pscustomobject]@{ AzureAccount = $AzureAccount; SubscriptionId = $AzureSubscriptionId }
}

function Connect-AzIotHubAndDpsToAdr {
    <#
    .SYNOPSIS
    Creates an ADR namespace, links an IoT Hub and a DPS to it, creates the certificate authority
    chain devices are issued certificates from, and returns the policy enrollments reference.

    .DESCRIPTION
    The hub and the DPS must have system-assigned identities. The namespace, its role grants and the
    link are one unit, retried as one; see Connect-AdrNamespace.

    .PARAMETER IotHub
    The hub, as read from ARM (id and identity.principalId are used).
    .PARAMETER Dps
    The DPS, as read from ARM (id and identity.principalId are used).

    .OUTPUTS
    [AdrPolicyReference]
    #>
    param(
        [Parameter(Mandatory = $true)][string]$SubscriptionId,
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Parameter(Mandatory = $true)][string]$Location,
        [Parameter(Mandatory = $true)]$IotHub,
        [Parameter(Mandatory = $true)]$Dps,
        [string]$NamespaceName = "azure-adr-ns",
        [string]$CertificateAuthorityName = "default",
        [string]$PolicyName = "azure-adr-policy"
    )

    # The namespace, its grants and the link are one unit, retried as one. The link runs as the
    # namespace identity, and an identity that never becomes usable to it cannot be waited out:
    # the recovery is to recreate the namespace, which mints a fresh one, and grant against that.
    for ($Cycle = 1; $Cycle -le $script:AdrLinkMaxCycles; $Cycle++) {
        $AzureAdrNamespace = New-AdrNamespace -SubscriptionId $SubscriptionId -ResourceGroup $ResourceGroup -NamespaceName $NamespaceName -Location $Location

        # Contributor is granted in BOTH directions for both resources: the link reads the hub and
        # the DPS as the namespace identity, and reads the namespace as theirs, and a grant missing
        # in either direction surfaces only as "the linked resource could not be read". The
        # namespace also needs it on ITSELF, because the device-create it runs writes its own
        # resource. On top of those sit the data-plane roles, and Azure Device Registry
        # Contributor, which is what lets the DPS write enrollments and issue a certificate for a
        # CSR: it already carries the issueCertificate data action, so no custom role is needed.
        $AdrNamespaceId = $AzureAdrNamespace.id
        $AdrNamespacePrincipalId = $AzureAdrNamespace.identity.principalId
        $IotHubPrincipalId = $IotHub.identity.principalId
        $DpsPrincipalId = $Dps.identity.principalId

        Write-Host "Assigning roles between the ADR namespace, the IoT Hub and the DPS (cycle $Cycle of $($script:AdrLinkMaxCycles))"
        @(
            @{ Assignee = $AdrNamespacePrincipalId; Role = $script:ContributorRoleId;           Scope = $IotHub.id },
            @{ Assignee = $IotHubPrincipalId;       Role = $script:ContributorRoleId;           Scope = $AdrNamespaceId },
            @{ Assignee = $AdrNamespacePrincipalId; Role = $script:ContributorRoleId;           Scope = $Dps.id },
            @{ Assignee = $DpsPrincipalId;          Role = $script:ContributorRoleId;           Scope = $AdrNamespaceId },
            @{ Assignee = $AdrNamespacePrincipalId; Role = $script:ContributorRoleId;           Scope = $AdrNamespaceId },
            @{ Assignee = $DpsPrincipalId;          Role = $script:AdrContributorRoleId;        Scope = $AdrNamespaceId },
            @{ Assignee = $DpsPrincipalId;          Role = $script:IotHubDataContributorRoleId; Scope = $IotHub.id },
            @{ Assignee = $AdrNamespacePrincipalId; Role = $script:IotHubDataContributorRoleId; Scope = $IotHub.id }
        ) | %{
            az role assignment create --assignee-object-id $_.Assignee --assignee-principal-type ServicePrincipal --role $_.Role --scope $_.Scope --only-show-errors | Out-Null
            Stop-OnError -Step "Assign role $($_.Role) on $($_.Scope)"
        }

        Wait-AzRoleAssignment `
            -PrincipalId "$($AdrNamespacePrincipalId)" `
            -Scope "$($IotHub.id)" `
            -RoleDefinitionIds @($script:ContributorRoleId, $script:IotHubDataContributorRoleId)

        Wait-AzRoleAssignment `
            -PrincipalId "$($AdrNamespacePrincipalId)" `
            -Scope "$($Dps.id)" `
            -RoleDefinitionIds @($script:ContributorRoleId)

        Wait-AzRoleAssignment `
            -PrincipalId "$($DpsPrincipalId)" `
            -Scope "$($AdrNamespaceId)" `
            -RoleDefinitionIds @($script:ContributorRoleId, $script:AdrContributorRoleId)

        # Device registration runs as the DPS identity against the hub, so its hub-scope grant
        # is waited for as well; only the namespace-scope ones were.
        Wait-AzRoleAssignment `
            -PrincipalId "$($DpsPrincipalId)" `
            -Scope "$($IotHub.id)" `
            -RoleDefinitionIds @($script:IotHubDataContributorRoleId)

        # Being readable is not the same as being enforced: the providers that check these grants
        # cache them, so the link is given a head start rather than racing the first attempt
        # against replication that has visibly only just finished. A recreated namespace starts
        # replicating from scratch, so the head start grows with the cycle.
        $HeadStart = 60 * $Cycle
        Write-Host "Waiting $HeadStart seconds for the new role assignments to take effect."
        Start-Sleep -Seconds $HeadStart

        try {
            Connect-AdrNamespace -NamespaceId $AdrNamespaceId -Location $Location -IotHubId $IotHub.id -DpsId $Dps.id -ExpectedPrincipalId $AdrNamespacePrincipalId
            break
        }
        catch {
            # Recreating is destructive and only helps the one case it exists for: an identity
            # that never becomes usable to the link. Connect-AdrNamespace already raises
            # everything else on the spot -- a rejected schema, a resource error, a timeout --
            # and those are surfaced rather than answered by deleting the namespace.
            if ($Cycle -ge $script:AdrLinkMaxCycles -or
                $_.Exception.Message -notmatch $script:AdrRolePropagationPattern) {
                throw
            }
            Write-Host "Linking did not succeed ($($_.Exception.Message)); recreating the namespace and retrying."
            Remove-AdrNamespace -NamespaceId $AdrNamespaceId
        }
    }

    # After the link, so that ADR has a hub to sync the issuing CA certificate to.
    New-AdrCertificateAuthority -NamespaceId $AdrNamespaceId -Location $Location `
        -CertificateAuthorityName $CertificateAuthorityName -PolicyName $PolicyName | Out-Null

    Sync-DpsAdrConfiguration -DpsId $Dps.id -Location $Location


    return [AdrPolicyReference]::new($NamespaceName, $CertificateAuthorityName, $PolicyName)
}

function New-AzIotDpsWithSystemIdentity {
    <#
    .SYNOPSIS
    Creates a DPS with a system-assigned identity through ARM, and returns it once provisioned.

    .DESCRIPTION
    The identity authenticates the DPS to an ADR namespace, or to a hub without local auth. It
    cannot be added afterwards: DPS rejects a managed-identity PATCH with IH400158.

    .PARAMETER Url
    ARM URL of the DPS, on the host Get-DpsArmHost gives for -Location.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$DpsName,
        [Parameter(Mandatory = $true)][string]$Location
    )

    # Re-read by New-AzArmResource: idScope and the identity's principalId are populated as it provisions.
    return New-AzArmResource -Url $Url -Step "Device Provisioning Service ($DpsName)" -Body @{
        location = $Location
        sku = @{ name = "S1"; capacity = 1 }
        identity = @{ type = "SystemAssigned" }
        properties = @{}
    }
}

function Set-TestEnvironmentDpsInfo {
    <#
    .SYNOPSIS
    Fills a DpsInfo with the host names, id scope and connection string of a DPS and the hub it
    provisions to.

    .PARAMETER Dps
    The DPS, as created (properties.deviceProvisioningHostName, serviceOperationsHostName, idScope).
    .PARAMETER LinkedIotHubFqdn
    Not read from the DPS: it is captured before the hub is attached, and a DPS linked to an ADR
    namespace does not carry its provisioning targets in its own list at all.
    #>
    param(
        [Parameter(Mandatory = $true)][DpsInfo]$DpsInfo,
        [Parameter(Mandatory = $true)]$Dps,
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Parameter(Mandatory = $true)][string]$DpsName,
        [Parameter(Mandatory = $true)][string]$LinkedIotHubFqdn
    )

    $DpsInfo.DeviceFqdn = $Dps.properties.deviceProvisioningHostName
    $DpsInfo.ServiceFqdn = $Dps.properties.serviceOperationsHostName
    $DpsInfo.IdScope = $Dps.properties.idScope
    $DpsInfo.LinkedIotHubs += $LinkedIotHubFqdn

    Write-Host "Getting DPS Connection String"
    $DpsInfo.ConnectionString = $(az iot dps connection-string show -g $ResourceGroup -n $DpsName --kt primary --pn provisioningserviceowner --query connectionString -o tsv)
    Stop-OnError -Step "Get DPS Connection String"
}

function New-FileUploadStorage {
    <#
    .SYNOPSIS
    Creates the storage account and container IoT Hub file upload uses, and returns the account's
    connection string.
    #>
    param(
        [string]$ResourceGroup,
        [string]$Location,
        [string]$StorageAccountName,
        [string]$ContainerName
    )

    Write-Host "Creating Azure Storage account ($StorageAccountName)"
    # --allow-blob-public-access is explicit: when omitted the CLI leaves the property out of the
    # request, and a policy requiring it to be set then denies the account (RequestDisallowedByPolicy).
    # The create can fail with StorageAccountOperationInProgress (409) while the account's own creation
    # is still running; repeating the same create succeeds once it completes.
    Invoke-WithRetry -Step "Creating Azure Storage account" -RetryOnPattern "$($script:ArmTransientPattern)|StorageAccountOperationInProgress" -Command {
        az storage account create --name "$StorageAccountName" --resource-group "$ResourceGroup" --location "$Location" --sku Standard_LRS --kind StorageV2 --allow-blob-public-access false --only-show-errors | Out-Null
    } | Out-Null

    Write-Host "Creating Azure Storage container ($ContainerName on $StorageAccountName)"
    az storage container create --name $ContainerName --account-name "$StorageAccountName" --only-show-errors | Out-Null
    Stop-OnError -Step "Creating Azure Storage container"

    Write-Host "Getting Azure Storage account connection string"
    $ConnectionString = $(az storage account show-connection-string --name "$StorageAccountName" --resource-group "$ResourceGroup" --query connectionString -o tsv)
    Stop-OnError -Step "Getting Azure Storage account connection string"

    return $ConnectionString
}

function Resolve-AzIotResourceAfterFailedCreate {
    <#
    .SYNOPSIS
    Before retrying a failed 'az iot hub create' or 'az iot dps create', returns the resource if the
    failed attempt still left it Active, or deletes what it left otherwise.

    .DESCRIPTION
    A create that fails server-side (e.g. IH500019) can leave the resource behind, and the CLI's
    name-availability check would then refuse the retry. Returns $null when nothing is left to reuse.
    Throws if listing or deleting fails, so the caller's retry policy judges that error instead.
    #>
    param(
        [Parameter(Mandatory = $true)][ValidateSet('hub', 'dps')][string]$Type,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$ResourceGroup
    )

    # Parenthesized so Windows PowerShell 5.1, whose ConvertFrom-Json emits an array as one object, enumerates it.
    $Existing = (az iot $Type list --resource-group "$ResourceGroup" --only-show-errors | ConvertFrom-Json) | ?{ $_.name -eq $Name } | Select-Object -First 1
    if ($LASTEXITCODE -ne 0) {
        throw "Could not list 'az iot $Type' resources in $ResourceGroup."
    }
    if ($null -eq $Existing) {
        return $null
    }
    if ($Existing.properties.state -eq 'Active') {
        Write-Host "Reusing $Type $Name, which the failed attempt left Active."
        return $Existing
    }

    Write-Host "Deleting $Type $Name, which the failed attempt left in state '$($Existing.properties.state)'."
    az iot $Type delete --name "$Name" --resource-group "$ResourceGroup" --only-show-errors | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not delete $Type $Name."
    }
    return $null
}

function Grant-IotHubDataContributorToSignedInPrincipal {
    <#
    .SYNOPSIS
    Grants the signed-in Azure CLI principal IoT Hub Data Contributor on a hub, and returns once
    the hub's data plane accepts it.

    .DESCRIPTION
    Needed to manage devices on a hub created with local auth disabled. The principal's object id is
    read from its ARM access token, so no Microsoft Graph permission is needed.

    .PARAMETER SkipDataPlaneCheck
    Returns once the assignment is readable, without the az CLI data-plane check, which cannot
    address an MQTT v5 hub (its ARM hostName is empty).
    #>
    param(
        [Parameter(Mandatory = $true)]$AzureAccount,
        [Parameter(Mandatory = $true)][string]$IotHubId,
        [Parameter(Mandatory = $true)][string]$IotHubName,
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [switch]$SkipDataPlaneCheck
    )

    $SignedInPrincipal = Get-AzSignedInPrincipal -AzureAccount $AzureAccount
    $PrincipalId = $SignedInPrincipal.Id
    $PrincipalType = $SignedInPrincipal.Type

    Write-Host "Assigning IoT Hub Data Contributor on $IotHubName to the signed-in $PrincipalType ($PrincipalId)"
    az role assignment create --assignee-object-id $PrincipalId --assignee-principal-type $PrincipalType --role $script:IotHubDataContributorRoleId --scope $IotHubId --only-show-errors | Out-Null
    Stop-OnError -Step "Assign IoT Hub Data Contributor on $IotHubName to the signed-in principal"
    Wait-AzRoleAssignment -PrincipalId $PrincipalId -Scope $IotHubId -RoleDefinitionIds @($script:IotHubDataContributorRoleId)
    if ($SkipDataPlaneCheck) {
        return
    }

    Invoke-WithRetry -Step "Reach the $IotHubName data plane with Entra ID" -RetryOnPattern $script:DataPlaneAccessDeniedPattern -MaxAttempts 6 -InitialDelaySeconds 20 -Command {
        az iot hub device-identity list --hub-name "$IotHubName" --resource-group "$ResourceGroup" --auth-type login --top 1 --only-show-errors | Out-Null
    } | Out-Null
}

function Grant-IotHubDataContributorToServicePrincipals {
    <#
    .SYNOPSIS
    Grants service principals, e.g. CI service connections, IoT Hub Data Contributor on a hub,
    unless they hold it already. Does not wait for the grants to apply.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$IotHubId,
        [string[]]$ServicePrincipalIds = @()
    )

    foreach ($ServicePrincipalId in @($ServicePrincipalIds | ?{ $_ } | Select-Object -Unique)) {
        Add-AzRoleAssignmentIfMissing -PrincipalId $ServicePrincipalId -PrincipalType ServicePrincipal `
            -RoleDefinitionId $script:IotHubDataContributorRoleId -Scope $IotHubId | Out-Null
    }
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
            throw "Device Provisioning Service ($($AzureDps.name)) does not have linked IoT hubs"
        }

        $IotHubName = $LinkedIotHubNames[0]
    } elseif ($IotHubName -notin $LinkedIotHubNames) {
        throw "IoT Hub $IotHubName is not linked to $($AzureDps.name)"
    }

    $AzureIoTHub = az iot hub show --resource-group "$ResourceGroup" --name "$IotHubName" | ConvertFrom-Json
    $TestEnvInfo.IotHub.LocalAuthDisabled = [bool]$AzureIoTHub.properties.disableLocalAuth
    $IotHubAuthArgs = @(if ($TestEnvInfo.IotHub.LocalAuthDisabled) { '--auth-type', 'login' })

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
    $IotHubDevices = az iot hub device-identity list --hub-name $IotHubName --resource-group $ResourceGroup @IotHubAuthArgs | ConvertFrom-Json
    Stop-OnError -Step "Retrieve IoT Hub's Device Identities"

    foreach ($Device in $IotHubDevices) {
        if ($Device.authentication.type -eq "sas") {
            $DeviceIdentity = [IotHubSymmetricKeyIdentityInfo]::new(
                $Device.deviceId,
                $Device.authentication.symmetricKey.primaryKey,
                $Device.authentication.symmetricKey.secondaryKey,
                $(az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $Device.deviceId --kt primary @IotHubAuthArgs --query connectionString -o tsv),
                $(az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $Device.deviceId --kt secondary @IotHubAuthArgs --query connectionString -o tsv)
            )

            $TestEnvInfo.IotHub.Devices.SymmetricKey += $DeviceIdentity
        } elseif ($Device.authentication.type -eq "x509_thumbprint") {
            $ConnectionString = az iot hub device-identity connection-string show --resource-group $ResourceGroup --hub-name $IotHubName -d $Device.deviceId @IotHubAuthArgs | ConvertFrom-Json

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
    # FQDNs, not the short names used for selection above: this list is what an enrollment's iotHubs
    # is set from (DpsInfo.AddX509GroupEnrollment reads LinkedIotHubs[0]), and a short name there is
    # rejected. The ADR endpoints carry ARM resource ids, so the host name is read from the hub.
    foreach ($Name in $LinkedIotHubNames) {
        $TestEnvInfo.Dps.LinkedIotHubs += if ($Name -eq $IotHubName) {
            $AzureIoTHub.properties.hostName
        } else {
            az iot hub show --resource-group "$ResourceGroup" --name "$Name" --query properties.hostName -o tsv
        }
    }

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
