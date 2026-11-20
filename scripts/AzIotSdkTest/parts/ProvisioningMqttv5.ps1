

# <[Azure IoT MQTT v5 Test Environment Public Functions]>

function New-AzIotMqttv5TestEnvironment {
    <#
    .SYNOPSIS
    Creates an MQTT v5 IoT Hub and a Device Provisioning Service linked to it through an Azure Device
    Registry (ADR) namespace, for testing the SDKs' MQTT v5 support.

    .DESCRIPTION
    The hub is created with connectionProfile MqttV5, a route from device messages to the built-in
    endpoint and one MQTT v5 topic group. Everything on the hub goes through ARM at
    IOT_HUB_MQTTV5_API_VERSION (default 2026-10-01-preview): 'az iot hub' cannot address such a hub
    (its ARM hostName is empty), and its update commands write the hub back at an older api-version,
    which drops connectionProfile and mqttV5Settings.

    The DPS is created first, so a subscription at its DPS quota fails before the slower hub is made.
    Both get a system-assigned identity and are linked to a new ADR namespace with a certificate
    authority, as New-AzIotTestEnvironment -EnableCertificateManagement does.

    Enrollments and devices are not created.

    .PARAMETER AzureLocation
    Azure location for the resources. Default is "eastus2euap".
    .PARAMETER AzureSubscriptionId
    Azure subscription ID. If not provided, the current Azure CLI session default subscription is used.
    .PARAMETER ResourceGroup
    Name of the resource group. Created if it does not exist; its tags are updated otherwise.
    .PARAMETER ResourceGroupTags
    Tags for the resource group.
    .PARAMETER DpsName
    Name of the Device Provisioning Service.
    .PARAMETER IotHubName
    Name of the IoT Hub.
    .PARAMETER TopicGroupId
    Id of the hub's MQTT v5 topic group.
    .PARAMETER TopicTemplates
    Topic templates of that group: 1 to 10, '{deviceId}' the only variable, and none starting with
    'ih', '+' or '#'.
    .PARAMETER EventHubConsumerGroups
    Consumer groups to create on the hub's built-in endpoint besides $Default.
    .PARAMETER DisableLocalAuth
    Creates the hub with local (shared access policy) authentication disabled, so its service APIs
    accept only Microsoft Entra ID. The signed-in principal is granted IoT Hub Data Contributor on the
    hub. The connection strings stay in the output for their host names only.
    .PARAMETER RouteTelemetryToEventHub
    Also routes device telemetry to an Event Hub of its own, read with Microsoft Entra ID only; see
    Add-AzIotEventHubTelemetryRoute. Telemetry keeps going to the built-in endpoint too.
    .PARAMETER TelemetryEventHubConsumerGroups
    Consumer groups to create on that Event Hub besides $Default.

    .OUTPUTS
    [TestEnvironmentInfo], with IotHub.ConnectionProfile 'MqttV5' and the hub's service and device
    host names in IotHub.ServiceFqdn and IotHub.DeviceFqdn.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotMqttv5TestEnvironment -DisableLocalAuth -RouteTelemetryToEventHub -TelemetryEventHubConsumerGroups e2e-0, e2e-1
    #>
    param(
        [string]$AzureLocation = "eastus2euap",
        [string]$AzureSubscriptionId = $null,
        [string]$ResourceGroup = $(New-AzureResourceGroupName),
        [Hashtable]$ResourceGroupTags = $null,
        [string]$DpsName = "dps-$(New-GuidString -NoDashes)",
        [string]$IotHubName = "iothub-$(New-GuidString -NoDashes)",
        [ValidatePattern('^[a-zA-Z0-9]([a-zA-Z0-9-]{0,45}[a-zA-Z0-9])?$')]
        [string]$TopicGroupId = "e2e",
        [ValidateCount(1, 10)]
        [string[]]$TopicTemplates = @('e2e/{deviceId}/#', 'e2e/shared/#'),
        [string[]]$EventHubConsumerGroups = @(),
        [switch]$DisableLocalAuth,
        [switch]$RouteTelemetryToEventHub,
        [string[]]$TelemetryEventHubConsumerGroups = @()
    )

    # Argument checks come before anything that touches Azure, so a bad invocation cannot leave a
    # resource group behind.
    if ($TelemetryEventHubConsumerGroups.Count -gt 0 -and -not $RouteTelemetryToEventHub) {
        throw "-TelemetryEventHubConsumerGroups requires -RouteTelemetryToEventHub."
    }
    foreach ($TopicTemplate in $TopicTemplates) {
        if ([string]::IsNullOrWhiteSpace($TopicTemplate) -or ($TopicTemplate -split '/')[0] -in 'ih', '+', '#' -or
            $TopicTemplate -cmatch '\{(?!deviceId\})[^}]*\}') {
            throw "Topic template '$TopicTemplate' is not allowed: it is empty, starts with 'ih', '+' or '#', or uses a variable other than {deviceId}."
        }
    }

    $ResourceGroupContext = Initialize-AzIotTestResourceGroup -AzureLocation $AzureLocation -AzureSubscriptionId $AzureSubscriptionId `
        -ResourceGroup $ResourceGroup -ResourceGroupTags $ResourceGroupTags
    $AzureAccount = $ResourceGroupContext.AzureAccount
    $AzureSubscriptionId = $ResourceGroupContext.SubscriptionId
    $ResourceGroupId = "/subscriptions/$AzureSubscriptionId/resourceGroups/$ResourceGroup"

    Write-Host "Creating Azure Device Provisioning Service ($DpsName, with a system-assigned identity)."
    $DpsUrl = "$(Get-DpsArmHost -Location $AzureLocation)$ResourceGroupId/providers/Microsoft.Devices/provisioningServices/$($DpsName)?api-version=$($script:DpsControlPlaneApiVersion)"
    $AzureDps = New-AzIotDpsWithSystemIdentity -Url $DpsUrl -DpsName $DpsName -Location $AzureLocation

    $IotHubId = "$ResourceGroupId/providers/Microsoft.Devices/IotHubs/$IotHubName"
    $IotHubUrl = "https://management.azure.com$($IotHubId)?api-version=$($script:IotHubMqttv5ApiVersion)"
    $TopicGroups = @(@{ topicGroupId = $TopicGroupId; topicTemplates = @($TopicTemplates) })
    Write-Host "Creating Azure IoT Hub ($IotHubName, MQTT v5)."
    $AzureIoTHub = New-AzArmResource -Url $IotHubUrl -Step "IoT Hub ($IotHubName)" -RetryOnPattern $script:IotTransientPattern -Body @{
        location = $AzureLocation
        sku = @{ name = "S1"; capacity = 1 }
        identity = @{ type = "SystemAssigned" }
        properties = @{
            connectionProfile = "MqttV5"
            disableLocalAuth = [bool]$DisableLocalAuth
            minTlsVersion = "1.2"
            # The service rejects an enabled fallback route to the built-in endpoint on an MQTT v5
            # hub, so telemetry reaches it through an explicit route.
            routing = @{ routes = @(@{ name = $script:BuiltInEndpointRouteName; source = "DeviceMessages"; condition = "true"
                endpointNames = @("events"); isEnabled = $true }) }
            mqttV5Settings = @{ topicGroups = $TopicGroups }
        }
    } -Condition { param($Hub) $Hub.properties.state -eq 'Active' }
    if ("$($AzureIoTHub.properties.connectionProfile)" -ne 'MqttV5') {
        throw "IoT Hub $IotHubName was created with connectionProfile '$($AzureIoTHub.properties.connectionProfile)', not MqttV5."
    }

    if ($DisableLocalAuth) {
        Grant-IotHubDataContributorToSignedInPrincipal -AzureAccount $AzureAccount -IotHubId $AzureIoTHub.id -IotHubName $IotHubName `
            -ResourceGroup $ResourceGroup -SkipDataPlaneCheck
    }

    $AzureAdrPolicy = Connect-AzIotHubAndDpsToAdr -SubscriptionId $AzureSubscriptionId -ResourceGroup $ResourceGroup `
        -Location $AzureLocation -IotHub $AzureIoTHub -Dps $AzureDps

    $ConsumerGroupsUrl = "https://management.azure.com$IotHubId/eventHubEndpoints/events/ConsumerGroups"
    $ExistingConsumerGroups = @((Invoke-AzRest -Url "$($ConsumerGroupsUrl)?api-version=$($script:IotHubMqttv5ApiVersion)").value | %{ $_.name })
    foreach ($ConsumerGroup in @($EventHubConsumerGroups | ?{ $_ -notin $ExistingConsumerGroups })) {
        Write-Host "Creating consumer group ($ConsumerGroup on the built-in endpoint of $IotHubName)"
        Invoke-WithRetry -Step "Create consumer group ($ConsumerGroup)" -RetryOnPattern "$($script:ArmTransientPattern)|$($script:IotTransientPattern)" -Command {
            Invoke-AzRest -Method PUT -Url "$ConsumerGroupsUrl/$($ConsumerGroup)?api-version=$($script:IotHubMqttv5ApiVersion)" -Body @{ properties = @{ name = $ConsumerGroup } }
        } | Out-Null
    }

    $TestEnvInfo = [TestEnvironmentInfo]::new()
    if ($RouteTelemetryToEventHub) {
        $TestEnvInfo.IotHub.TelemetryEventHub = Add-AzIotEventHubTelemetryRoute -ResourceGroup $ResourceGroup -IotHubName $IotHubName `
            -Location $AzureLocation -ConsumerGroups $TelemetryEventHubConsumerGroups -KeepBuiltInEndpointRoute -IotHubApiVersion $script:IotHubMqttv5ApiVersion
    }

    # Last, after every full write of the hub: the ADR link is one, and it can drop the topic groups.
    $AzureIoTHub = Invoke-AzRest -Url $IotHubUrl
    if (-not (Test-IotHubTopicGroups -IotHub $AzureIoTHub -TopicGroups $TopicGroups)) {
        $AzureIoTHub = Update-AzArmResource -Url $IotHubUrl -Step "Restore the MQTT v5 topic group '$TopicGroupId' on $IotHubName" `
            -RetryOnPattern $script:IotTransientPattern -Update {
            param($Hub)
            $Hub.properties.mqttV5Settings = @{ topicGroups = $TopicGroups }
        } -Condition {
            param($Hub)
            $Hub.properties.state -eq 'Active' -and (Test-IotHubTopicGroups -IotHub $Hub -TopicGroups $TopicGroups)
        }
    }

    $ServiceFqdn = $AzureIoTHub.properties.serviceHostName
    $Events = $AzureIoTHub.properties.eventHubEndpoints.events
    Write-Host "Getting IoT Hub Connection Strings"
    $OwnerKey = @((Invoke-AzRest -Method POST -Url "https://management.azure.com$IotHubId/listkeys?api-version=$($script:IotHubMqttv5ApiVersion)").value) |
        ?{ $_.keyName -eq 'iothubowner' } | Select-Object -First 1
    if ($null -eq $OwnerKey) {
        throw "IoT Hub $IotHubName has no iothubowner shared access policy."
    }

    $TestEnvInfo.AzureResourceGroup = $ResourceGroup
    $TestEnvInfo.AdrPolicy = $AzureAdrPolicy
    $TestEnvInfo.IotHub.ConnectionProfile = 'MqttV5'
    $TestEnvInfo.IotHub.ServiceFqdn = $ServiceFqdn
    $TestEnvInfo.IotHub.DeviceFqdn = $AzureIoTHub.properties.deviceHostName
    $TestEnvInfo.IotHub.LocalAuthDisabled = [bool]$DisableLocalAuth
    $TestEnvInfo.IotHub.ConnectionString = "HostName=$ServiceFqdn;SharedAccessKeyName=iothubowner;SharedAccessKey=$($OwnerKey.primaryKey)"
    $TestEnvInfo.IotHub.EventHub.ConnectionString = "Endpoint=$($Events.endpoint);SharedAccessKeyName=iothubowner;SharedAccessKey=$($OwnerKey.primaryKey);EntityPath=$($Events.path)"
    $TestEnvInfo.IotHub.EventHub.CompatibleName = $Events.path
    $TestEnvInfo.IotHub.EventHub.PartitionCount = $Events.partitionCount
    $TestEnvInfo.IotHub.EventHub.ConsumerGroups = @(@('$Default') + $ExistingConsumerGroups + $EventHubConsumerGroups | ?{ $_ } | Select-Object -Unique)

    $TestEnvInfo.Dps.ResourceGroup = $ResourceGroup
    $TestEnvInfo.Dps.AdrPolicy = $AzureAdrPolicy
    Set-TestEnvironmentDpsInfo -DpsInfo $TestEnvInfo.Dps -Dps $AzureDps -ResourceGroup $ResourceGroup -DpsName $DpsName -LinkedIotHubFqdn $ServiceFqdn

    return $TestEnvInfo
}

function Test-IotHubTopicGroups {
    <#
    .SYNOPSIS
    Tells whether an MQTT v5 hub, as read from ARM, has exactly these topic groups, templates in order.
    #>
    param(
        [Parameter(Mandatory = $true)]$IotHub,
        [Parameter(Mandatory = $true)][Hashtable[]]$TopicGroups
    )

    $Actual = @($IotHub.properties.mqttV5Settings.topicGroups | ?{ $null -ne $_ })
    if ($Actual.Count -ne $TopicGroups.Count) {
        return $false
    }
    foreach ($Expected in $TopicGroups) {
        $Group = $Actual | ?{ $_.topicGroupId -ceq $Expected.topicGroupId } | Select-Object -First 1
        if ($null -eq $Group -or (@($Group.topicTemplates) -join "`n") -cne (@($Expected.topicTemplates) -join "`n")) {
            return $false
        }
    }
    return $true
}
