
# <[Device Telemetry Routing Functions]>

# Azure Event Hubs Data Sender (the hub's identity) and Data Receiver (the test readers).
$script:EventHubsDataSenderRoleId = "2b629674-e913-4c01-ae53-ef4638d8f975"
$script:EventHubsDataReceiverRoleId = "a638d3c7-ab3a-418d-83e6-5f17a39d4fde"
# Event Hubs can take up to five minutes to enforce a new role assignment.
$script:EventHubsRolePropagationSeconds = 300
# An identity-based routing endpoint is refused until the hub's Data Sender grant applies.
$script:RoutingEndpointRolePropagationPattern = 'Unauthorized|Forbidden|AuthorizationFailed|authoriz|permission|IH40[013]\d{3}'

function Add-AzIotEventHubTelemetryRoute {
    <#
    .SYNOPSIS
    Routes an IoT Hub's device telemetry to an Event Hub that accepts only Microsoft Entra ID, and
    returns where to read it.

    .DESCRIPTION
    The built-in Event Hub-compatible endpoint accepts only shared access keys, which a hub created
    with -DisableLocalAuth refuses. This creates an Event Hubs namespace with local auth disabled
    and TLS 1.2, an Event Hub with the given consumer groups, and a route from the hub to it. The
    hub sends with its system-assigned identity (Azure Event Hubs Data Sender); the signed-in
    principal and -ReaderServicePrincipalIds read with Microsoft Entra ID (Azure Event Hubs Data
    Receiver).

    Safe to run again on the same hub and namespace: what already exists is kept. A routing endpoint
    of the same name that targets another Event Hub or does not use the hub's system identity fails
    the call, and so does a route of the same name that does not send all device messages to its
    endpoint.

    .PARAMETER ResourceGroup
    Resource group of the IoT Hub; the namespace is created in it too.
    .PARAMETER IotHubName
    Name of the IoT Hub whose device telemetry is routed.
    .PARAMETER Location
    Azure location of the namespace. Defaults to the resource group's location.
    .PARAMETER NamespaceName
    Event Hubs namespace name. Defaults to a random one; pass a fixed name to update an environment
    in place.
    .PARAMETER EventHubName
    Name of the Event Hub, and of the hub's routing endpoint and route. Default is "telemetry".
    .PARAMETER PartitionCount
    Partitions of a new Event Hub. Default is 4. Ignored when the Event Hub exists.
    .PARAMETER ConsumerGroups
    Consumer groups to create besides $Default. Event Hubs allows five readers per partition per
    consumer group, so give each parallel test job its own.
    .PARAMETER ReaderServicePrincipalIds
    Object ids of service principals that also read the Event Hub, e.g. CI service connections.
    .PARAMETER KeepBuiltInEndpointRoute
    Also routes device telemetry to the built-in endpoint. Once a hub has any route, the built-in
    endpoint receives only what a route sends it, so readers of the built-in endpoint need this.

    .OUTPUTS
    [TelemetryEventHubInfo]. Its ReadableAfterUnixSeconds is when the newest of the role assignments
    above applies, so readers granted by an earlier call still wait for it.

    .EXAMPLE
    PS> $TestEnvInfo.IotHub.TelemetryEventHub = Add-AzIotEventHubTelemetryRoute -ResourceGroup $Rg -IotHubName $Hub -ConsumerGroups e2e-0, e2e-1
    #>
    param(
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Parameter(Mandatory = $true)][string]$IotHubName,
        [string]$Location = $null,
        # 6 to 50 characters, starting with a letter.
        [ValidatePattern('^[A-Za-z][A-Za-z0-9-]{4,48}[A-Za-z0-9]$')]
        [string]$NamespaceName = "ehns-$(New-GuidString -NoDashes -MaxLength 20)",
        [string]$EventHubName = "telemetry",
        [ValidateRange(1, 32)][int]$PartitionCount = 4,
        [string[]]$ConsumerGroups = @(),
        [string[]]$ReaderServicePrincipalIds = @(),
        [switch]$KeepBuiltInEndpointRoute
    )

    if ([string]::IsNullOrWhiteSpace($Location)) {
        $Location = az group show --name "$ResourceGroup" --query location -o tsv --only-show-errors
        Stop-OnError -Step "Get the location of resource group $ResourceGroup"
    }

    Write-Host "Creating Event Hubs namespace ($NamespaceName, local auth disabled)"
    # Create is a PUT: it also brings an existing namespace back to these settings.
    $Namespace = Invoke-WithRetry -Step "Create Event Hubs namespace ($NamespaceName)" -RetryOnPattern $script:ArmTransientPattern -Command {
        az eventhubs namespace create --name "$NamespaceName" --resource-group "$ResourceGroup" --location "$Location" `
            --sku Standard --disable-local-auth true --minimum-tls-version 1.2 --only-show-errors | ConvertFrom-Json
    }
    $FullyQualifiedNamespace = ([uri]$Namespace.serviceBusEndpoint).Host

    # Parenthesized so Windows PowerShell 5.1, whose ConvertFrom-Json emits an array as one object, enumerates it.
    $EventHub = (az eventhubs eventhub list --namespace-name "$NamespaceName" --resource-group "$ResourceGroup" --only-show-errors |
        ConvertFrom-Json) | ?{ $_.name -eq $EventHubName } | Select-Object -First 1
    Stop-OnError -Step "List the Event Hubs in $NamespaceName"
    if ($null -eq $EventHub) {
        Write-Host "Creating Event Hub ($EventHubName, $PartitionCount partitions)"
        $EventHub = Invoke-WithRetry -Step "Create Event Hub ($EventHubName)" -RetryOnPattern $script:ArmTransientPattern -Command {
            az eventhubs eventhub create --name "$EventHubName" --namespace-name "$NamespaceName" --resource-group "$ResourceGroup" `
                --partition-count $PartitionCount --only-show-errors | ConvertFrom-Json
        }
    }

    $ExistingConsumerGroups = @(az eventhubs eventhub consumer-group list --eventhub-name "$EventHubName" --namespace-name "$NamespaceName" `
        --resource-group "$ResourceGroup" --query "[].name" -o tsv --only-show-errors)
    Stop-OnError -Step "List the consumer groups of $EventHubName"
    foreach ($ConsumerGroup in @($ConsumerGroups | ?{ $_ -notin $ExistingConsumerGroups })) {
        Write-Host "Creating consumer group ($ConsumerGroup on $EventHubName)"
        Invoke-WithRetry -Step "Create consumer group ($ConsumerGroup)" -RetryOnPattern $script:ArmTransientPattern -Command {
            az eventhubs eventhub consumer-group create --name "$ConsumerGroup" --eventhub-name "$EventHubName" `
                --namespace-name "$NamespaceName" --resource-group "$ResourceGroup" --only-show-errors | Out-Null
        } | Out-Null
    }

    Write-Host "Assigning a system identity to IoT Hub ($IotHubName)"
    $IotHubPrincipalId = Invoke-WithRetry -Step "Assign a system identity to $IotHubName" -RetryOnPattern "$($script:ArmTransientPattern)|$($script:IdentityTransientPattern)" -Command {
        az iot hub identity assign --name "$IotHubName" --resource-group "$ResourceGroup" --system-assigned --query principalId -o tsv --only-show-errors
    }

    $SignedInPrincipal = Get-AzSignedInPrincipal
    $Grants = @(@{ Id = $IotHubPrincipalId; Type = 'ServicePrincipal'; Role = $script:EventHubsDataSenderRoleId }) +
        @(@{ Id = $SignedInPrincipal.Id; Type = $SignedInPrincipal.Type; Role = $script:EventHubsDataReceiverRoleId }) +
        @($ReaderServicePrincipalIds | ?{ $_ -and $_ -ne $SignedInPrincipal.Id } | %{ @{ Id = $_; Type = 'ServicePrincipal'; Role = $script:EventHubsDataReceiverRoleId } })
    $ReadableAfter = [DateTimeOffset]::UtcNow
    foreach ($Grant in $Grants) {
        $GrantedOn = Add-AzRoleAssignmentIfMissing -PrincipalId $Grant.Id -PrincipalType $Grant.Type -RoleDefinitionId $Grant.Role -Scope $EventHub.id
        $GrantApplies = $GrantedOn.AddSeconds($script:EventHubsRolePropagationSeconds)
        if ($GrantApplies -gt $ReadableAfter) {
            $ReadableAfter = $GrantApplies
        }
    }

    $Routing = az iot hub show --name "$IotHubName" --resource-group "$ResourceGroup" --query properties.routing --only-show-errors | ConvertFrom-Json
    Stop-OnError -Step "Get the routing of $IotHubName"
    $EndpointUri = "sb://$FullyQualifiedNamespace"
    $Endpoint = @($Routing.endpoints.eventHubs) | ?{ $null -ne $_ -and $_.name -eq $EventHubName } | Select-Object -First 1
    if ($null -eq $Endpoint) {
        Write-Host "Creating routing endpoint ($EventHubName on $IotHubName, system identity)"
        Invoke-WithRetry -Step "Create routing endpoint ($EventHubName)" -RetryOnPattern "$($script:ArmTransientPattern)|$($script:RoutingEndpointRolePropagationPattern)" -MaxAttempts 5 -InitialDelaySeconds 20 -Command {
            az iot hub message-endpoint create eventhub --hub-name "$IotHubName" --resource-group "$ResourceGroup" --endpoint-name "$EventHubName" `
                --endpoint-uri "$EndpointUri" --entity-path "$EventHubName" --identity '[system]' --only-show-errors | Out-Null
        } | Out-Null
    } else {
        # The Data Sender grant above is for the system identity only.
        $UsesSystemIdentity = $Endpoint.authenticationType -eq 'identityBased' -and [string]::IsNullOrEmpty("$($Endpoint.identity.userAssignedIdentity)")
        if ("$($Endpoint.endpointUri)".TrimEnd('/') -ne $EndpointUri -or $Endpoint.entityPath -ne $EventHubName -or -not $UsesSystemIdentity) {
            throw "IoT Hub $IotHubName already has an endpoint '$EventHubName' for $($Endpoint.endpointUri)$($Endpoint.entityPath) " +
                "(authentication: $($Endpoint.authenticationType) $($Endpoint.identity.userAssignedIdentity)), not $EndpointUri/$EventHubName with its system identity."
        }
    }

    # The built-in route first, so its readers never miss telemetry.
    $Routes = @(@{ Name = $EventHubName; Endpoint = $EventHubName })
    if ($KeepBuiltInEndpointRoute) {
        $Routes = @(@{ Name = 'builtin-events'; Endpoint = 'events' }) + $Routes
    }
    foreach ($Route in $Routes) {
        $ExistingRoute = @($Routing.routes) | ?{ $null -ne $_ -and $_.name -eq $Route.Name } | Select-Object -First 1
        if ($null -ne $ExistingRoute) {
            $Condition = "$($ExistingRoute.condition)".Trim()
            if ($ExistingRoute.source -ne 'DeviceMessages' -or (@($ExistingRoute.endpointNames) -join ',') -ne $Route.Endpoint -or
                $ExistingRoute.isEnabled -ne $true -or ($Condition -and $Condition -ne 'true')) {
                throw "IoT Hub $IotHubName already has a route '$($Route.Name)' that does not send all device messages to '$($Route.Endpoint)' " +
                    "(source $($ExistingRoute.source), endpoints $(@($ExistingRoute.endpointNames) -join ','), enabled $($ExistingRoute.isEnabled), condition '$Condition')."
            }
            continue
        }
        Write-Host "Routing device messages to $($Route.Endpoint) on $IotHubName"
        Invoke-WithRetry -Step "Create route ($($Route.Name))" -RetryOnPattern $script:ArmTransientPattern -Command {
            az iot hub message-route create --hub-name "$IotHubName" --resource-group "$ResourceGroup" --route-name "$($Route.Name)" `
                --endpoint-name "$($Route.Endpoint)" --source-type DeviceMessages --enabled true --only-show-errors | Out-Null
        } | Out-Null
    }

    $TelemetryEventHub = [TelemetryEventHubInfo]::new()
    $TelemetryEventHub.FullyQualifiedNamespace = $FullyQualifiedNamespace
    $TelemetryEventHub.Name = $EventHubName
    $TelemetryEventHub.PartitionCount = $EventHub.partitionCount
    $TelemetryEventHub.ConsumerGroups = @(@('$Default') + $ExistingConsumerGroups + $ConsumerGroups | ?{ $_ } | Select-Object -Unique)
    $TelemetryEventHub.ReadableAfterUnixSeconds = $ReadableAfter.ToUnixTimeSeconds()
    return $TelemetryEventHub
}
