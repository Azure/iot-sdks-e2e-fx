

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

    # Argument checks come before anything that touches Azure, so a bad invocation cannot leave a
    # resource group behind.
    if ($EnableCertificateManagement -eq $true -and $NoDps -eq $true) {
        throw "Certificate management requires a Device Provisioning Service; -NoDps and -EnableCertificateManagement are mutually exclusive."
    }

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

    # Certificate management provisions the same three resources as the reference E2E harness for
    # this feature does, in the same shape: a plain S1 hub and a plain DPS, each with its own
    # system-assigned identity, and an ADR namespace they are both attached to afterwards through the
    # namespace's own endpoints. Nothing is pointed at anything else as it is created, which is what
    # the retired public-preview model did.
    if ($EnableCertificateManagement -eq $true) {
        $AzureAdrNamespaceName = "azure-adr-ns"
        $AzureAdrPolicyName = "azure-adr-policy"
        $AzureAdrCertificateAuthorityName = "default"

        # Created through ARM so it comes up with a system-assigned identity and local auth left on,
        # which is the shape ADR links. S1, not GEN2: a GEN2 hub carries the namespace in its own
        # properties, which is the retired model.
        Write-Host "Creating Azure IoT Hub ($IotHubName, with certificate management support)."
        $IotHubUrl = "https://management.azure.com/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Devices/IotHubs/$($IotHubName)?api-version=$($script:IotHubApiVersion)"
        Invoke-AzRest -Method PUT -Url $IotHubUrl -Body @{
            location = $AzureLocation
            sku = @{ name = "S1"; capacity = 1 }
            identity = @{ type = "SystemAssigned" }
            properties = @{ disableLocalAuth = $false; minTlsVersion = "1.2" }
        } | Out-Null
        Wait-AzProvisioningState -Url $IotHubUrl -Step "IoT Hub ($IotHubName)" -TimeoutSeconds 1200
        $AzureIoTHub = Invoke-AzRest -Url $IotHubUrl
    } else {
        Write-Host "Creating Azure IoT Hub ($IotHubName)."
        $AzureIoTHub = az iot hub create --name "$IotHubName" --resource-group "$ResourceGroup" --location "$AzureLocation" --mintls "1.2" | ConvertFrom-Json
        Stop-OnError -Step "Create Azure IoT Hub"
    }

    if ($NoDps -eq $false) {
        if ($EnableCertificateManagement -eq $true) {
            # Created through ARM rather than 'az iot dps create' so it comes up WITH a system-assigned
            # identity, which is what authenticates it to the ADR namespace. The identity cannot be
            # added afterwards: DPS rejects a managed-identity PATCH with IH400158. Confined to this
            # branch so ordinary provisioning keeps the CLI create and does not take a dependency on
            # a preview api-version it has no use for.
            Write-Host "Creating Azure Device Provisioning Service ($DpsName, with certificate management support)."
            $DpsUrl = "$(Get-DpsArmHost -Location $AzureLocation)/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Devices/provisioningServices/$($DpsName)?api-version=$($script:DpsControlPlaneApiVersion)"
            Invoke-AzRest -Method PUT -Url $DpsUrl -Body @{
                location = $AzureLocation
                sku = @{ name = "S1"; capacity = 1 }
                identity = @{ type = "SystemAssigned" }
                properties = @{}
            } | Out-Null
            Wait-AzProvisioningState -Url $DpsUrl -Step "Device Provisioning Service ($DpsName)" -TimeoutSeconds 1200
            # Re-read: idScope and the identity's principalId are populated as it provisions.
            $AzureDps = Invoke-AzRest -Url $DpsUrl
        } else {
            Write-Host "Creating Azure Device Provisioning Service ($DpsName)."
            $AzureDps = az iot dps create --name "$DpsName" --resource-group "$ResourceGroup" --location "$AzureLocation" | ConvertFrom-Json
            Stop-OnError -Step "Create Device Provisioning Service"
        }
    }

    if ($EnableCertificateManagement -eq $true) {
        # The namespace, its grants and the link are one unit, retried as one. The link runs as the
        # namespace identity, and an identity that never becomes usable to it cannot be waited out:
        # the recovery is to recreate the namespace, which mints a fresh one, and grant against that.
        for ($Cycle = 1; $Cycle -le $script:AdrLinkMaxCycles; $Cycle++) {
            $AzureAdrNamespace = New-AdrNamespace -SubscriptionId $AzureSubscriptionId -ResourceGroup $ResourceGroup -NamespaceName $AzureAdrNamespaceName -Location $AzureLocation

            # Contributor is granted in BOTH directions for both resources: the link reads the hub and
            # the DPS as the namespace identity, and reads the namespace as theirs, and a grant missing
            # in either direction surfaces only as "the linked resource could not be read". The
            # namespace also needs it on ITSELF, because the device-create it runs writes its own
            # resource. On top of those sit the data-plane roles, and Azure Device Registry
            # Contributor, which is what lets the DPS write enrollments and issue a certificate for a
            # CSR: it already carries the issueCertificate data action, so no custom role is needed.
            $AdrNamespaceId = $AzureAdrNamespace.id
            $AdrNamespacePrincipalId = $AzureAdrNamespace.identity.principalId
            $IotHubPrincipalId = $AzureIoTHub.identity.principalId
            $DpsPrincipalId = $AzureDps.identity.principalId

            Write-Host "Assigning roles between the ADR namespace, the IoT Hub and the DPS (cycle $Cycle of $($script:AdrLinkMaxCycles))"
            @(
                @{ Assignee = $AdrNamespacePrincipalId; Role = $script:ContributorRoleId;           Scope = $AzureIoTHub.id },
                @{ Assignee = $IotHubPrincipalId;       Role = $script:ContributorRoleId;           Scope = $AdrNamespaceId },
                @{ Assignee = $AdrNamespacePrincipalId; Role = $script:ContributorRoleId;           Scope = $AzureDps.id },
                @{ Assignee = $DpsPrincipalId;          Role = $script:ContributorRoleId;           Scope = $AdrNamespaceId },
                @{ Assignee = $AdrNamespacePrincipalId; Role = $script:ContributorRoleId;           Scope = $AdrNamespaceId },
                @{ Assignee = $DpsPrincipalId;          Role = $script:AdrContributorRoleId;        Scope = $AdrNamespaceId },
                @{ Assignee = $DpsPrincipalId;          Role = $script:IotHubDataContributorRoleId; Scope = $AzureIoTHub.id },
                @{ Assignee = $AdrNamespacePrincipalId; Role = $script:IotHubDataContributorRoleId; Scope = $AzureIoTHub.id }
            ) | %{
                az role assignment create --assignee-object-id $_.Assignee --assignee-principal-type ServicePrincipal --role $_.Role --scope $_.Scope --only-show-errors | Out-Null
                Stop-OnError -Step "Assign role $($_.Role) on $($_.Scope)"
            }

            Wait-AzRoleAssignment `
                -PrincipalId "$($AdrNamespacePrincipalId)" `
                -Scope "$($AzureIoTHub.id)" `
                -RoleDefinitionIds @($script:ContributorRoleId, $script:IotHubDataContributorRoleId)

            Wait-AzRoleAssignment `
                -PrincipalId "$($AdrNamespacePrincipalId)" `
                -Scope "$($AzureDps.id)" `
                -RoleDefinitionIds @($script:ContributorRoleId)

            Wait-AzRoleAssignment `
                -PrincipalId "$($DpsPrincipalId)" `
                -Scope "$($AdrNamespaceId)" `
                -RoleDefinitionIds @($script:ContributorRoleId, $script:AdrContributorRoleId)

            # Device registration runs as the DPS identity against the hub, so its hub-scope grant
            # is waited for as well; only the namespace-scope ones were.
            Wait-AzRoleAssignment `
                -PrincipalId "$($DpsPrincipalId)" `
                -Scope "$($AzureIoTHub.id)" `
                -RoleDefinitionIds @($script:IotHubDataContributorRoleId)

            # Being readable is not the same as being enforced: the providers that check these grants
            # cache them, so the link is given a head start rather than racing the first attempt
            # against replication that has visibly only just finished. A recreated namespace starts
            # replicating from scratch, so the head start grows with the cycle.
            $HeadStart = 60 * $Cycle
            Write-Host "Waiting $HeadStart seconds for the new role assignments to take effect."
            Start-Sleep -Seconds $HeadStart

            try {
                Connect-AdrNamespace -NamespaceId $AdrNamespaceId -Location $AzureLocation -IotHubId $AzureIoTHub.id -DpsId $AzureDps.id -ExpectedPrincipalId $AdrNamespacePrincipalId
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
        New-AdrCertificateAuthority -NamespaceId $AdrNamespaceId -Location $AzureLocation `
            -CertificateAuthorityName $AzureAdrCertificateAuthorityName -PolicyName $AzureAdrPolicyName | Out-Null

        Sync-DpsAdrConfiguration -DpsId $AzureDps.id -Location $AzureLocation

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
            throw "Device Provisioning Service ($($AzureDps.name)) does not have linked IoT hubs"
        }

        $IotHubName = $LinkedIotHubNames[0]
    } elseif ($IotHubName -notin $LinkedIotHubNames) {
        throw "IoT Hub $IotHubName is not linked to $($AzureDps.name)"
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
