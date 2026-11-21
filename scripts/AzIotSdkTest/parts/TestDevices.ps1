# <[Stale test devices on permanent test environments]>

# IoT Hub service API (device registry and queries).
$script:IotHubServiceApiVersion = if ($env:IOT_HUB_SERVICE_API_VERSION) { $env:IOT_HUB_SERVICE_API_VERSION } else { "2021-04-12" }
# Bulk registry operations take at most 100 devices.
$script:IotHubBulkDeleteSize = 100
# ADR namespaces and registry devices; registry devices exist from 2026-11-01.
$script:AdrRegistryDeviceApiVersion = if ($env:ADR_REGISTRY_DEVICE_API_VERSION) { $env:ADR_REGISTRY_DEVICE_API_VERSION } else { "2026-11-01" }
# ADR deletes are asynchronous: they are polled this often, and fail after this long without one completing.
$script:AdrDeviceDeletePollSeconds = 20
$script:AdrDeviceDeleteTimeoutSeconds = 900
$script:ArmEndpoint = "https://management.azure.com"
$script:ArmProvidersApiVersion = "2021-04-01"
$script:IotHubEntraResource = "https://iothubs.azure.net"

function Remove-AzIotStaleTestDevices {
    <#
    .SYNOPSIS
    Deletes the test devices that runs left on a permanent test environment, with their DPS
    registrations.

    .DESCRIPTION
    Test runs on a permanent environment register devices on its hub, often through its DPS, and
    leave them when they fail or are canceled. This finds them on the hub and deletes them.

    A device is selected when its id matches -DeviceIdPattern and its twin carries every
    -TwinTags value; at least one of the two is required. A selected device is then kept when:

      * it is in -ExcludeDeviceIds;
      * it is connected;
      * its latest activity (last activity, status update, or twin update) is less than
        -MinimumAgeHours old, so a running test keeps its devices;
      * it has none of those times, so its age is unknown.

    Devices registered through an Azure Device Registry (ADR) policy also have an ADR device, in
    the ADR namespace linked to the hub or the DPS; those namespaces are found in the hub's
    subscription. With -DeviceIdPattern, an ADR device matching it whose hub device is gone (a test
    deleted only that) is selected too, aged by its ADR create or update time; only in a namespace
    linked to nothing else, since another hub's devices could be in a shared one.

    Each selected device's DPS registration (-DpsName) is deleted first, then its ADR devices, then
    the device on the hub. The hub is where devices are found, so a device whose DPS registration or
    ADR device could not be deleted is kept on the hub for the next run to find; the cmdlet fails
    after trying them all.

    The hub and ADR are called with Microsoft Entra ID (IoT Hub Data Contributor, or Registry
    Contributor, on the hub; Microsoft.DeviceRegistry/namespaces/read and
    namespaces/registryDevices/read and /delete on the ADR namespaces, e.g. Azure Device Registry
    Administrator, not Azure Device Registry Contributor), so it works with local authentication
    disabled. The DPS is called with its 'provisioningserviceowner' key.

    .PARAMETER ResourceGroup
    Resource group of the hub and the DPS.
    .PARAMETER IotHubName
    Name of the hub.
    .PARAMETER DpsName
    Name of the DPS whose registrations are deleted too. Omit it for devices created on the hub.
    .PARAMETER DeviceIdPattern
    Case-sensitive regular expression the device id must match, e.g. '^horton-\d+-'.
    .PARAMETER TwinTags
    Twin tags the device must have, all of them, e.g. @{ e2eSuite = 'horton' }. Set them on the
    devices of an enrollment group with Add-AzIotSharedEnrollmentGroups -InitialTwinTags. A key may
    be a dotted path to a nested tag.
    .PARAMETER MinimumAgeHours
    Hours since a device's latest activity before it is deleted. Default is 6.
    .PARAMETER ExcludeDeviceIds
    Device ids never deleted, e.g. the environment's own pinned devices.

    .OUTPUTS
    One object per selected device: DeviceId, LastActivityUtc, Result (Deleted, AlreadyDeleted,
    Kept: <reason>, WhatIf, or Failed: <error>), OnHub, and AdrDeviceIds (its ADR device resource
    ids).

    .EXAMPLE
    Remove-AzIotStaleTestDevices -ResourceGroup <rg> -IotHubName <hub> -DpsName <dps> `
        -TwinTags @{ e2eSuite = 'horton' } -ExcludeDeviceIds pinned-device-1 -WhatIf
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true)][string]$ResourceGroup,
        [Parameter(Mandatory = $true)][string]$IotHubName,
        [string]$DpsName = $null,
        [string]$DeviceIdPattern = $null,
        [Hashtable]$TwinTags = $null,
        [ValidateRange(1, 8760)][int]$MinimumAgeHours = 6,
        [string[]]$ExcludeDeviceIds = @()
    )

    $HasPattern = -not [string]::IsNullOrWhiteSpace($DeviceIdPattern)
    if (-not $HasPattern -and ($null -eq $TwinTags -or $TwinTags.Count -eq 0)) {
        throw "Give -DeviceIdPattern, -TwinTags or both: without them every device on the hub would be selected."
    }
    if ($HasPattern) {
        # An invalid pattern fails here rather than on the first device.
        [void][regex]::new($DeviceIdPattern)
    }

    $Query = New-IotHubDeviceQuery -TwinTags $TwinTags
    $IotHub = Get-IotHubResource -ResourceGroup $ResourceGroup -IotHubName $IotHubName
    $IotHubHostName = Get-IotHubServiceHostName -IotHub $IotHub
    Write-Host "Querying the devices of $IotHubHostName ($Query)."
    $Twins = @(Get-IotHubDeviceTwins -IotHubHostName $IotHubHostName -Query $Query)

    $Cutoff = [DateTime]::UtcNow.AddHours(-$MinimumAgeHours)
    $Devices = New-Object System.Collections.Generic.List[object]
    foreach ($Twin in $Twins) {
        $DeviceId = [string]$Twin.deviceId
        if ($HasPattern -and $DeviceId -cnotmatch $DeviceIdPattern) { continue }
        $LastActivityUtc = Get-TestDeviceLastActivityUtc -Twin $Twin
        $Result = if ($Twin.connectionState -eq 'Connected') { "Kept: connected" }
            else { Get-StaleTestDeviceKeepReason -DeviceId $DeviceId -LastActivityUtc $LastActivityUtc -Cutoff $Cutoff -MinimumAgeHours $MinimumAgeHours -ExcludeDeviceIds $ExcludeDeviceIds }
        $Devices.Add([pscustomobject]@{ DeviceId = $DeviceId; LastActivityUtc = $LastActivityUtc; Result = $Result; OnHub = $true; AdrDeviceIds = @() })
    }
    Write-Host "$($Twins.Count) device(s) queried, $($Devices.Count) selected."

    $SubscriptionId = ($IotHub.id -split '/')[2]
    $LinkedResourceIds = @($IotHub.id)
    if (-not [string]::IsNullOrWhiteSpace($DpsName)) {
        $LinkedResourceIds += "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Devices/provisioningServices/$DpsName"
    }
    $AdrNamespaces = @(Find-AdrNamespacesLinkedTo -SubscriptionId $SubscriptionId -ResourceIds $LinkedResourceIds)
    $AdrNamespaceIds = @($AdrNamespaces | %{ $_.Id })
    if ($AdrNamespaceIds.Count -gt 0) {
        Write-Host "ADR namespace(s) linked to the hub or the DPS: $(($AdrNamespaces | %{ ($_.Id -split '/')[-1] + $(if ($_.LinkedToOthers) { ' (also linked to others)' }) }) -join ', ')."
        Add-AdrDevicesToStaleTestDevices -Devices $Devices -AdrNamespaceIds $AdrNamespaceIds -IotHubHostName $IotHubHostName `
            -OrphanAdrNamespaceIds @($AdrNamespaces | ?{ -not $_.LinkedToOthers } | %{ $_.Id }) `
            -DeviceIdPattern $(if ($HasPattern) { $DeviceIdPattern }) -Cutoff $Cutoff -MinimumAgeHours $MinimumAgeHours -ExcludeDeviceIds $ExcludeDeviceIds
    }
    $Devices = $Devices.ToArray()

    $Stale = @($Devices | ?{ $null -eq $_.Result })
    Write-Host "$($Devices.Count) device(s) selected, $($Stale.Count) stale, $(@($Stale | ?{ -not $_.OnHub }).Count) of them only in ADR."
    $Devices | ?{ $null -ne $_.Result } | Group-Object Result | %{ Write-Host "  $($_.Count) $($_.Name.ToLowerInvariant())." }

    if ($Stale.Count -eq 0) {
        return $Devices
    }

    $Target = "$($Stale.Count) device(s) on $IotHubHostName" + $(if ($DpsName) { ", their registrations on DPS $DpsName" }) +
        $(if ($AdrNamespaceIds.Count -gt 0) { ", their ADR devices" })
    if (-not $PSCmdlet.ShouldProcess($Target, "Delete")) {
        $Stale | %{ $_.Result = "WhatIf" }
        return $Devices
    }

    if (-not [string]::IsNullOrWhiteSpace($DpsName)) {
        Remove-DpsDeviceRegistrations -ResourceGroup $ResourceGroup -DpsName $DpsName -Devices $Stale
    }
    $AdrStale = @($Stale | ?{ $null -eq $_.Result -and $_.AdrDeviceIds.Count -gt 0 })
    if ($AdrStale.Count -gt 0) {
        Remove-AdrRegistryDevices -Devices $AdrStale -AdrNamespaceIds $AdrNamespaceIds
    }
    Remove-IotHubDevices -IotHubHostName $IotHubHostName -Devices @($Stale | ?{ $null -eq $_.Result -and $_.OnHub })
    # Deleting an ADR device can delete its hub device too.
    $AdrStale | ?{ $null -eq $_.Result -or $_.Result -eq 'AlreadyDeleted' } | %{ $_.Result = 'Deleted' }

    $Failed = @($Stale | ?{ "$($_.Result)" -like 'Failed*' })
    Write-Host "$(@($Stale | ?{ $_.Result -eq 'Deleted' }).Count) deleted, $(@($Stale | ?{ $_.Result -eq 'AlreadyDeleted' }).Count) already deleted, $($Failed.Count) failed."
    if ($Failed.Count -gt 0) {
        $Failed | %{ Write-Warning "$($_.DeviceId): $($_.Result)" }
        throw "$($Failed.Count) stale test device(s) could not be deleted: $(($Failed | %{ $_.DeviceId }) -join ', ')."
    }
    return $Devices
}

function Get-TestDeviceLastActivityUtc {
    <#
    .SYNOPSIS
    The latest of a device twin's last activity, status update and twin update times, in UTC;
    $null when it has none.
    #>
    param($Twin)

    $Times = @(
        $Twin.lastActivityTime
        $Twin.statusUpdateTime
        $Twin.properties.desired.'$metadata'.'$lastUpdated'
        $Twin.properties.reported.'$metadata'.'$lastUpdated'
    ) | %{ ConvertTo-UtcDateTime -Value $_ } | ?{ $null -ne $_ -and $_.Year -gt 2000 }

    return ($Times | Sort-Object -Descending | Select-Object -First 1)
}

function Get-StaleTestDeviceKeepReason {
    <#
    .SYNOPSIS
    Why a disconnected test device is kept ('Kept: ...'), or $null when it is stale.
    #>
    param(
        [string]$DeviceId,
        $LastActivityUtc,
        [DateTime]$Cutoff,
        [int]$MinimumAgeHours,
        [string[]]$ExcludeDeviceIds
    )

    if ($ExcludeDeviceIds -ccontains $DeviceId) { return "Kept: excluded" }
    if ($null -eq $LastActivityUtc) { return "Kept: no activity time" }
    if ($LastActivityUtc -gt $Cutoff) { return "Kept: active within $MinimumAgeHours h" }
    return $null
}

function New-IotHubDeviceQuery {
    <#
    .SYNOPSIS
    The hub query of every device twin, or of those carrying all of -TwinTags.
    #>
    param([Hashtable]$TwinTags)

    if ($null -eq $TwinTags -or $TwinTags.Count -eq 0) {
        return "SELECT * FROM devices"
    }
    $Conditions = foreach ($Name in ($TwinTags.Keys | Sort-Object)) {
        if ("$Name" -notmatch '^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$') {
            throw "Twin tag '$Name' is not a name or a dotted path of names."
        }
        "tags.$Name = '$("$($TwinTags[$Name])".Replace("'", "''"))'"
    }
    return "SELECT * FROM devices WHERE $($Conditions -join ' AND ')"
}

function Get-IotHubResource {
    <#
    .SYNOPSIS
    A hub's ARM resource, read at an API version that knows MQTT v5 hubs.
    #>
    param(
        [string]$ResourceGroup,
        [string]$IotHubName
    )

    $IotHub = az resource show --resource-group $ResourceGroup --name $IotHubName --resource-type Microsoft.Devices/IotHubs `
        --api-version $script:IotHubMqttv5ApiVersion -o json --only-show-errors | ConvertFrom-Json
    Stop-OnError -Step "Read IoT Hub $IotHubName"
    return $IotHub
}

function Get-IotHubServiceHostName {
    <#
    .SYNOPSIS
    Host name of a hub's service API: its serviceHostName on an MQTT v5 hub, else its hostName.
    #>
    param($IotHub)

    $Properties = $IotHub.properties
    $HostName = if ($Properties.iotHubDetails.gatewayVersion -eq 'V2' -and $Properties.serviceHostName) { $Properties.serviceHostName }
        elseif ($Properties.hostName) { $Properties.hostName }
        else { $Properties.serviceHostName }
    if ([string]::IsNullOrWhiteSpace($HostName)) {
        throw "IoT Hub $($IotHub.name) has no host name."
    }
    return $HostName
}

function Get-IotHubDeviceTwins {
    <#
    .SYNOPSIS
    Runs a device twin query on a hub's service API with Microsoft Entra ID, every page of it.
    #>
    param(
        [string]$IotHubHostName,
        [string]$Query
    )

    $Uri = "https://$IotHubHostName/devices/query?api-version=$($script:IotHubServiceApiVersion)"
    $Continuation = $null
    do {
        $Headers = @{}
        if ($Continuation) { $Headers['x-ms-continuation'] = $Continuation }
        $Response = Invoke-ServiceRestRequest -Method POST -Uri $Uri -Body @{ query = $Query } -Headers $Headers `
            -Authorization { Get-EntraAccessToken -Resource $script:IotHubEntraResource }
        if ($Response.Status -ne 200) {
            throw "Device query on $IotHubHostName failed: HTTP $($Response.Status) $($Response.Text)"
        }
        @($Response.Json) | ?{ $null -ne $_ }
        $Continuation = $Response.Continuation
    } while ($Continuation)
}

function Find-AdrNamespacesLinkedTo {
    <#
    .SYNOPSIS
    The ADR namespaces in a subscription with a messaging or provisioning endpoint on one of
    -ResourceIds: Id, and LinkedToOthers when an endpoint is on another resource. None when ADR is
    not registered on the subscription.
    #>
    param(
        [string]$SubscriptionId,
        [string[]]$ResourceIds
    )

    $Uri = "$($script:ArmEndpoint)/subscriptions/$SubscriptionId/providers/Microsoft.DeviceRegistry/namespaces?api-version=$($script:AdrRegistryDeviceApiVersion)"
    while ($Uri) {
        $Response = Invoke-ServiceRestRequest -Method GET -Uri $Uri -Authorization { Get-EntraAccessToken -Resource $script:ArmEndpoint }
        if ($Response.Status -ne 200) {
            $Code = if ($null -ne $Response.Json -and $Response.Json.PSObject.Properties['error']) { [string]$Response.Json.error.code }
            # These codes also mean an unsupported api-version or location: no ADR only when it is unregistered.
            if ($Code -in 'MissingSubscriptionRegistration', 'NoRegisteredProviderFound', 'InvalidResourceType' -and
                (Get-ArmResourceProviderRegistrationState -SubscriptionId $SubscriptionId -ProviderNamespace 'Microsoft.DeviceRegistry') -in 'NotRegistered', 'Unregistered') {
                return
            }
            throw "Listing the ADR namespaces of subscription $SubscriptionId failed: HTTP $($Response.Status) $($Response.Text)"
        }
        foreach ($Namespace in @($Response.Json.value | ?{ $_ })) {
            $Endpoints = foreach ($Kind in 'messaging', 'provisioning') {
                $Group = $Namespace.properties.$Kind.endpoints
                if ($null -ne $Group) { $Group.PSObject.Properties | %{ [string]$_.Value.resourceId } }
            }
            $Endpoints = @($Endpoints | ?{ $_ })
            if (@($Endpoints | ?{ $ResourceIds -contains $_ }).Count -gt 0) {
                [pscustomobject]@{ Id = [string]$Namespace.id; LinkedToOthers = @($Endpoints | ?{ $ResourceIds -notcontains $_ }).Count -gt 0 }
            }
        }
        $Uri = [string]$Response.Json.nextLink
    }
}

function Get-ArmResourceProviderRegistrationState {
    <#
    .SYNOPSIS
    A resource provider's registration state on a subscription (Registered, NotRegistered, ...);
    NotRegistered when the cloud has no such provider.
    #>
    param(
        [string]$SubscriptionId,
        [string]$ProviderNamespace
    )

    $Response = Invoke-ServiceRestRequest -Method GET -Uri "$($script:ArmEndpoint)/subscriptions/$SubscriptionId/providers/$($ProviderNamespace)?api-version=$($script:ArmProvidersApiVersion)" `
        -Authorization { Get-EntraAccessToken -Resource $script:ArmEndpoint }
    if ($Response.Status -eq 404) { return 'NotRegistered' }
    if ($Response.Status -ne 200) {
        throw "Reading the registration of $ProviderNamespace on subscription $SubscriptionId failed: HTTP $($Response.Status) $($Response.Text)"
    }
    return [string]$Response.Json.registrationState
}

function Get-AdrRegistryDevices {
    <#
    .SYNOPSIS
    Every registry device of the ADR namespaces: NamespaceId, ResourceId, DeviceId (its
    externalDeviceId, or its name) and LastChangeUtc (its latest ARM create or update time).
    #>
    param([string[]]$AdrNamespaceIds)

    foreach ($NamespaceId in $AdrNamespaceIds) {
        $Uri = "$($script:ArmEndpoint)$NamespaceId/registryDevices?api-version=$($script:AdrRegistryDeviceApiVersion)"
        while ($Uri) {
            $Response = Invoke-ServiceRestRequest -Method GET -Uri $Uri -Authorization { Get-EntraAccessToken -Resource $script:ArmEndpoint }
            if ($Response.Status -ne 200) {
                throw "Listing the devices of ADR namespace $NamespaceId failed: HTTP $($Response.Status) $($Response.Text)"
            }
            foreach ($AdrDevice in @($Response.Json.value | ?{ $_ })) {
                $DeviceId = [string]$AdrDevice.properties.externalDeviceId
                if (-not $DeviceId) { $DeviceId = [string]$AdrDevice.name }
                $LastChangeUtc = @($AdrDevice.systemData.createdAt, $AdrDevice.systemData.lastModifiedAt) |
                    %{ ConvertTo-UtcDateTime -Value $_ } | ?{ $null -ne $_ } | Sort-Object -Descending | Select-Object -First 1
                [pscustomobject]@{ NamespaceId = $NamespaceId; ResourceId = [string]$AdrDevice.id; DeviceId = $DeviceId; LastChangeUtc = $LastChangeUtc }
            }
            $Uri = [string]$Response.Json.nextLink
        }
    }
}

function Add-AdrDevicesToStaleTestDevices {
    <#
    .SYNOPSIS
    Sets each test device's AdrDeviceIds and, with -DeviceIdPattern, adds the matching ADR devices
    of -OrphanAdrNamespaceIds whose hub device is gone, with OnHub $false.
    #>
    param(
        [System.Collections.Generic.List[object]]$Devices,
        [string[]]$AdrNamespaceIds,
        [string[]]$OrphanAdrNamespaceIds,
        [string]$IotHubHostName,
        [string]$DeviceIdPattern,
        [DateTime]$Cutoff,
        [int]$MinimumAgeHours,
        [string[]]$ExcludeDeviceIds
    )

    $AdrDevicesById = New-Object 'System.Collections.Generic.Dictionary[string, System.Collections.Generic.List[object]]' ([StringComparer]::Ordinal)
    foreach ($AdrDevice in @(Get-AdrRegistryDevices -AdrNamespaceIds $AdrNamespaceIds)) {
        if (-not $AdrDevicesById.ContainsKey($AdrDevice.DeviceId)) { $AdrDevicesById[$AdrDevice.DeviceId] = New-Object System.Collections.Generic.List[object] }
        $AdrDevicesById[$AdrDevice.DeviceId].Add($AdrDevice)
    }

    $Known = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
    foreach ($Device in $Devices) {
        [void]$Known.Add($Device.DeviceId)
        if ($AdrDevicesById.ContainsKey($Device.DeviceId)) { $Device.AdrDeviceIds = @($AdrDevicesById[$Device.DeviceId] | %{ $_.ResourceId }) }
    }
    if ([string]::IsNullOrEmpty($DeviceIdPattern)) { return }

    $InSharedNamespace = 0
    foreach ($DeviceId in @($AdrDevicesById.Keys | Sort-Object)) {
        if ($Known.Contains($DeviceId) -or $DeviceId -cnotmatch $DeviceIdPattern) { continue }
        # In a namespace also linked to another hub, a 404 here does not make the device an orphan.
        if (@($AdrDevicesById[$DeviceId] | ?{ $OrphanAdrNamespaceIds -notcontains $_.NamespaceId }).Count -gt 0) {
            $InSharedNamespace++
            continue
        }
        # A device not queried may still be on the hub, without the twin tags asked for.
        $Response = Invoke-ServiceRestRequest -Method GET -Uri "https://$IotHubHostName/devices/$([uri]::EscapeDataString($DeviceId))?api-version=$($script:IotHubServiceApiVersion)" `
            -Authorization { Get-EntraAccessToken -Resource $script:IotHubEntraResource }
        if ($Response.Status -eq 200) { continue }
        if ($Response.Status -ne 404) {
            throw "Reading device $DeviceId on $IotHubHostName failed: HTTP $($Response.Status) $($Response.Text)"
        }
        $LastActivityUtc = $AdrDevicesById[$DeviceId] | %{ $_.LastChangeUtc } | ?{ $null -ne $_ } | Sort-Object -Descending | Select-Object -First 1
        $Devices.Add([pscustomobject]@{
            DeviceId = $DeviceId
            LastActivityUtc = $LastActivityUtc
            Result = Get-StaleTestDeviceKeepReason -DeviceId $DeviceId -LastActivityUtc $LastActivityUtc -Cutoff $Cutoff -MinimumAgeHours $MinimumAgeHours -ExcludeDeviceIds $ExcludeDeviceIds
            OnHub = $false
            AdrDeviceIds = @($AdrDevicesById[$DeviceId] | %{ $_.ResourceId })
        })
    }
    if ($InSharedNamespace -gt 0) {
        Write-Host "$InSharedNamespace ADR device(s) not on the hub left alone: their namespace is also linked to other resources."
    }
}

function Remove-AdrRegistryDevices {
    <#
    .SYNOPSIS
    Deletes each device's ADR devices and waits for them to be gone; sets Result to
    'Failed: ...' where that fails.

    .DESCRIPTION
    Every delete is submitted first, then all are awaited together by listing the namespaces:
    awaiting each long-running delete in turn would take hours. The deletes still pending
    $script:AdrDeviceDeleteTimeoutSeconds after the last one completed fail.
    #>
    param(
        [object[]]$Devices,
        [string[]]$AdrNamespaceIds
    )

    $Pending = New-Object 'System.Collections.Generic.Dictionary[string, object]' ([StringComparer]::OrdinalIgnoreCase)
    $Deleted = 0
    foreach ($Device in $Devices) {
        foreach ($ResourceId in $Device.AdrDeviceIds) {
            $Response = Invoke-ServiceRestRequest -Method DELETE -Uri "$($script:ArmEndpoint)$($ResourceId)?api-version=$($script:AdrRegistryDeviceApiVersion)" `
                -Authorization { Get-EntraAccessToken -Resource $script:ArmEndpoint }
            # 409: another operation, usually an earlier delete, is in progress; the listing settles it.
            if ($Response.Status -in 202, 409) { $Pending[$ResourceId] = $Device }
            elseif ($Response.Status -in 200, 204, 404) { $Deleted++ }
            else { $Device.Result = "Failed: ADR device: HTTP $($Response.Status) $($Response.Text)" }
        }
    }

    $LastProgressUtc = [DateTime]::UtcNow
    while ($Pending.Count -gt 0) {
        Start-Sleep -Seconds $script:AdrDeviceDeletePollSeconds
        $Present = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
        Get-AdrRegistryDevices -AdrNamespaceIds $AdrNamespaceIds | %{ [void]$Present.Add($_.ResourceId) }
        foreach ($ResourceId in @($Pending.Keys)) {
            if ($Present.Contains($ResourceId)) { continue }
            [void]$Pending.Remove($ResourceId)
            $Deleted++
            $LastProgressUtc = [DateTime]::UtcNow
        }
        Write-Host "ADR: $Deleted device(s) deleted, $($Pending.Count) pending."
        if ($Pending.Count -gt 0 -and ([DateTime]::UtcNow - $LastProgressUtc).TotalSeconds -ge $script:AdrDeviceDeleteTimeoutSeconds) {
            foreach ($ResourceId in $Pending.Keys) {
                $Pending[$ResourceId].Result = "Failed: ADR device: $ResourceId still present $($script:AdrDeviceDeleteTimeoutSeconds) s after the last delete completed"
            }
            break
        }
    }
    Write-Host "ADR: $Deleted device(s) deleted."
}

function Remove-DpsDeviceRegistrations {
    <#
    .SYNOPSIS
    Deletes the DPS registration of each device; sets Result to 'Failed: ...' where that fails.
    A device with no registration is not a failure.
    #>
    param(
        [string]$ResourceGroup,
        [string]$DpsName,
        [object[]]$Devices
    )

    $ConnectionString = Get-DpsServiceConnectionString -ResourceGroup $ResourceGroup -DpsName $DpsName
    $DpsHostName = Get-ConnectionStringHostName -ConnectionString $ConnectionString
    # Not a closure: that would leave the module scope, where New-DpsServiceSasToken is.
    $Authorization = { New-DpsServiceSasToken -ConnectionString $ConnectionString }

    $Deleted = 0
    foreach ($Device in $Devices) {
        $Uri = "https://$DpsHostName/registrations/$([uri]::EscapeDataString($Device.DeviceId))?api-version=$($script:DpsEnrollmentApiVersion)"
        $Response = Invoke-ServiceRestRequest -Method DELETE -Uri $Uri -Authorization $Authorization
        if ($Response.Status -in 200, 204) { $Deleted++ }
        elseif ($Response.Status -ne 404) {
            $Device.Result = "Failed: DPS registration: HTTP $($Response.Status) $($Response.Text)"
        }
    }
    Write-Host "DPS ${DpsName}: $Deleted registration(s) deleted."
}

function Remove-IotHubDevices {
    <#
    .SYNOPSIS
    Deletes devices from a hub with Microsoft Entra ID, $script:IotHubBulkDeleteSize at a time, and
    sets each one's Result.

    .DESCRIPTION
    A device the bulk delete does not take is deleted on its own; one already gone counts as
    deleted. Bulk deletes run one at a time: the registry operations quota is per hub.
    #>
    param(
        [string]$IotHubHostName,
        [object[]]$Devices
    )

    for ($Start = 0; $Start -lt $Devices.Count; $Start += $script:IotHubBulkDeleteSize) {
        $Chunk = @($Devices[$Start..([Math]::Min($Start + $script:IotHubBulkDeleteSize, $Devices.Count) - 1)])
        $Body = @($Chunk | %{ @{ id = $_.DeviceId; importMode = 'delete' } })
        $Response = Invoke-ServiceRestRequest -Method POST -Uri "https://$IotHubHostName/devices?api-version=$($script:IotHubServiceApiVersion)" `
            -Body $Body -Authorization { Get-EntraAccessToken -Resource $script:IotHubEntraResource }

        # A bulk answer lists the devices it did not delete; anything else says nothing about them.
        $Retry = $Chunk
        if ($Response.Status -in 200, 400 -and $null -ne $Response.Json -and $null -ne $Response.Json.PSObject.Properties['isSuccessful']) {
            $Errors = @{}
            @($Response.Json.errors) | ?{ $_ } | %{ $Errors[[string]$_.deviceId] = [string]$_.errorCode }
            $Retry = @(foreach ($Device in $Chunk) {
                if (-not $Errors.ContainsKey($Device.DeviceId)) { $Device.Result = 'Deleted' }
                elseif ($Errors[$Device.DeviceId] -eq 'DeviceNotFound') { $Device.Result = 'AlreadyDeleted' }
                else { $Device }
            })
        } else {
            Write-Warning "Bulk delete on $IotHubHostName failed (HTTP $($Response.Status)); deleting its $($Chunk.Count) device(s) one at a time."
        }

        foreach ($Device in $Retry) {
            $Response = Invoke-ServiceRestRequest -Method DELETE -Headers @{ 'If-Match' = '"*"' } `
                -Uri "https://$IotHubHostName/devices/$([uri]::EscapeDataString($Device.DeviceId))?api-version=$($script:IotHubServiceApiVersion)" `
                -Authorization { Get-EntraAccessToken -Resource $script:IotHubEntraResource }
            $Device.Result = if ($Response.Status -in 200, 204) { 'Deleted' }
                elseif ($Response.Status -eq 404) { 'AlreadyDeleted' }
                else { "Failed: hub: HTTP $($Response.Status) $($Response.Text)" }
        }
    }
}

function Get-EntraAccessToken {
    <#
    .SYNOPSIS
    A Microsoft Entra ID authorization header for -Resource, reused until 3 minutes before it
    expires (one minute when the CLI does not say).
    #>
    param([Parameter(Mandatory = $true)][string]$Resource)

    if ($null -eq $script:EntraAccessTokens) { $script:EntraAccessTokens = @{} }
    $Cached = $script:EntraAccessTokens[$Resource]
    if ($null -eq $Cached -or [DateTime]::UtcNow -gt $Cached.RenewUtc) {
        $Token = az account get-access-token --resource $Resource --query "{accessToken:accessToken, expiresOn:expires_on}" -o json --only-show-errors | ConvertFrom-Json
        Stop-OnError -Step "Get a Microsoft Entra ID token for $Resource"
        $RenewUtc = if ($Token.expiresOn) { [DateTimeOffset]::FromUnixTimeSeconds([long]$Token.expiresOn).UtcDateTime.AddMinutes(-3) }
            else { [DateTime]::UtcNow.AddMinutes(1) }
        $Cached = @{ Header = "Bearer $($Token.accessToken)"; RenewUtc = $RenewUtc }
        $script:EntraAccessTokens[$Resource] = $Cached
    }
    return $Cached.Header
}

function Invoke-ServiceRestRequest {
    <#
    .SYNOPSIS
    Calls a service API, retrying network errors, 408, 429 and 5xx, and returns Status (0 for a
    network error), Text, Json and Continuation (the x-ms-continuation header). Never throws on a
    failed request, so callers can go on with the rest.

    .PARAMETER Authorization
    Returns the Authorization header; called for each attempt, so a token can be renewed.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][scriptblock]$Authorization,
        $Body = $null,
        [Hashtable]$Headers = @{},
        [int]$MaxAttempts = 6
    )

    $RequestHeaders = @{}
    foreach ($Name in $Headers.Keys) { $RequestHeaders[$Name] = $Headers[$Name] }
    $Content = if ($null -ne $Body) { ConvertTo-Json -InputObject $Body -Depth 10 -Compress }

    for ($Attempt = 1; ; $Attempt++) {
        $RequestHeaders['Authorization'] = & $Authorization
        $Response = Send-ServiceHttpRequest -Method $Method -Uri $Uri -Headers $RequestHeaders -Content $Content
        $Retriable = $Response.Status -eq 0 -or $Response.Status -in 408, 429 -or $Response.Status -ge 500
        if (-not $Retriable -or $Attempt -ge $MaxAttempts) {
            $Json = $null
            if (-not [string]::IsNullOrWhiteSpace($Response.Text)) {
                try { $Json = ConvertFrom-Json -InputObject $Response.Text } catch { $Json = $null }
            }
            return [pscustomobject]@{ Status = $Response.Status; Text = $Response.Text; Json = $Json; Continuation = $Response.Continuation }
        }
        $DelaySeconds = if ($Response.Status -eq 429) { 10 + (Get-Random -Maximum 20) } else { [Math]::Min(60, [Math]::Pow(2, $Attempt)) }
        Write-Host "$Method $($Uri -replace '\?.*'): HTTP $($Response.Status); retrying in $DelaySeconds s."
        Start-Sleep -Seconds $DelaySeconds
    }
}

function Send-ServiceHttpRequest {
    <#
    .SYNOPSIS
    One HTTP request: Status (0 for a network error), Text and Continuation. Works the same on
    Windows PowerShell 5.1, which has no -SkipHttpErrorCheck.
    #>
    param(
        [string]$Method,
        [string]$Uri,
        [Hashtable]$Headers,
        [string]$Content
    )

    $Request = @{ Method = $Method; Uri = $Uri; Headers = $Headers; UseBasicParsing = $true; TimeoutSec = 100 }
    if ($Content) {
        $Request.Body = [Text.Encoding]::UTF8.GetBytes($Content)
        $Request.ContentType = 'application/json; charset=utf-8'
    }

    $Status = 0
    $Text = $null
    $ResponseHeaders = $null
    try {
        $Response = Invoke-WebRequest @Request
        $Status = [int]$Response.StatusCode
        $Text = if ($Response.Content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($Response.Content) } else { [string]$Response.Content }
        $ResponseHeaders = $Response.Headers
    }
    catch {
        $ErrorResponse = if ($_.Exception.PSObject.Properties['Response']) { $_.Exception.Response }
        if ($null -eq $ErrorResponse) {
            $Text = $_.Exception.Message
        } else {
            $Status = [int]$ErrorResponse.StatusCode
            $Text = if ($_.ErrorDetails) { $_.ErrorDetails.Message } else { $_.Exception.Message }
        }
    }

    $Continuation = $null
    if ($null -ne $ResponseHeaders) {
        foreach ($Name in @($ResponseHeaders.Keys)) {
            if ($Name -ieq 'x-ms-continuation') { $Continuation = [string](@($ResponseHeaders[$Name])[0]) }
        }
    }
    return @{ Status = $Status; Text = $Text; Continuation = $Continuation }
}
