# <[Stale test devices on permanent test environments]>

# IoT Hub service API (device registry and queries).
$script:IotHubServiceApiVersion = if ($env:IOT_HUB_SERVICE_API_VERSION) { $env:IOT_HUB_SERVICE_API_VERSION } else { "2021-04-12" }
# Bulk registry operations take at most 100 devices.
$script:IotHubBulkDeleteSize = 100

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

    Each selected device's DPS registration (-DpsName) is deleted first, then the device on the
    hub. The hub is where devices are found, so a device whose DPS registration could not be
    deleted is kept on the hub for the next run to find; the cmdlet fails after trying them all.

    The hub is called with Microsoft Entra ID (it needs IoT Hub Data Contributor, or Registry
    Contributor), so it works with local authentication disabled. The DPS is called with its
    'provisioningserviceowner' key.

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
    One object per selected device: DeviceId, LastActivityUtc and Result (Deleted, AlreadyDeleted,
    Kept: <reason>, WhatIf, or Failed: <error>).

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
    $IotHubHostName = Get-IotHubServiceHostName -ResourceGroup $ResourceGroup -IotHubName $IotHubName
    Write-Host "Querying the devices of $IotHubHostName ($Query)."
    $Twins = @(Get-IotHubDeviceTwins -IotHubHostName $IotHubHostName -Query $Query)

    $Cutoff = [DateTime]::UtcNow.AddHours(-$MinimumAgeHours)
    $Devices = @(foreach ($Twin in $Twins) {
        $DeviceId = [string]$Twin.deviceId
        if ($HasPattern -and $DeviceId -cnotmatch $DeviceIdPattern) { continue }
        $LastActivityUtc = Get-TestDeviceLastActivityUtc -Twin $Twin
        $Result = if ($ExcludeDeviceIds -ccontains $DeviceId) { "Kept: excluded" }
            elseif ($Twin.connectionState -eq 'Connected') { "Kept: connected" }
            elseif ($null -eq $LastActivityUtc) { "Kept: no activity time" }
            elseif ($LastActivityUtc -gt $Cutoff) { "Kept: active within $MinimumAgeHours h" }
            else { $null }
        [pscustomobject]@{ DeviceId = $DeviceId; LastActivityUtc = $LastActivityUtc; Result = $Result }
    })
    $Stale = @($Devices | ?{ $null -eq $_.Result })
    Write-Host "$($Twins.Count) device(s) queried, $($Devices.Count) selected, $($Stale.Count) stale."
    $Devices | ?{ $null -ne $_.Result } | Group-Object Result | %{ Write-Host "  $($_.Count) $($_.Name.ToLowerInvariant())." }

    if ($Stale.Count -eq 0) {
        return $Devices
    }

    $Target = "$($Stale.Count) device(s) on $IotHubHostName" + $(if ($DpsName) { " and their registrations on DPS $DpsName" })
    if (-not $PSCmdlet.ShouldProcess($Target, "Delete")) {
        $Stale | %{ $_.Result = "WhatIf" }
        return $Devices
    }

    if (-not [string]::IsNullOrWhiteSpace($DpsName)) {
        Remove-DpsDeviceRegistrations -ResourceGroup $ResourceGroup -DpsName $DpsName -Devices $Stale
    }
    Remove-IotHubDevices -IotHubHostName $IotHubHostName -Devices @($Stale | ?{ $null -eq $_.Result })

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

function Get-IotHubServiceHostName {
    <#
    .SYNOPSIS
    Host name of a hub's service API: its serviceHostName on an MQTT v5 hub, else its hostName.
    #>
    param(
        [string]$ResourceGroup,
        [string]$IotHubName
    )

    $Properties = az resource show --resource-group $ResourceGroup --name $IotHubName --resource-type Microsoft.Devices/IotHubs `
        --api-version $script:IotHubMqttv5ApiVersion --query properties -o json --only-show-errors | ConvertFrom-Json
    Stop-OnError -Step "Read IoT Hub $IotHubName"

    $HostName = if ($Properties.iotHubDetails.gatewayVersion -eq 'V2' -and $Properties.serviceHostName) { $Properties.serviceHostName }
        elseif ($Properties.hostName) { $Properties.hostName }
        else { $Properties.serviceHostName }
    if ([string]::IsNullOrWhiteSpace($HostName)) {
        throw "IoT Hub $IotHubName has no host name."
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
            -Authorization { Get-IotHubAccessToken }
        if ($Response.Status -ne 200) {
            throw "Device query on $IotHubHostName failed: HTTP $($Response.Status) $($Response.Text)"
        }
        @($Response.Json) | ?{ $null -ne $_ }
        $Continuation = $Response.Continuation
    } while ($Continuation)
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
            -Body $Body -Authorization { Get-IotHubAccessToken }

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
                -Authorization { Get-IotHubAccessToken }
            $Device.Result = if ($Response.Status -in 200, 204) { 'Deleted' }
                elseif ($Response.Status -eq 404) { 'AlreadyDeleted' }
                else { "Failed: hub: HTTP $($Response.Status) $($Response.Text)" }
        }
    }
}

function Get-IotHubAccessToken {
    <#
    .SYNOPSIS
    A Microsoft Entra ID authorization header for the IoT Hub service API, reused until 3 minutes
    before it expires (one minute when the CLI does not say).
    #>
    if ($null -eq $script:IotHubAccessToken -or [DateTime]::UtcNow -gt $script:IotHubAccessTokenRenewUtc) {
        $Token = az account get-access-token --resource https://iothubs.azure.net --query "{accessToken:accessToken, expiresOn:expires_on}" -o json --only-show-errors | ConvertFrom-Json
        Stop-OnError -Step "Get a Microsoft Entra ID token for IoT Hub"
        $script:IotHubAccessToken = "Bearer $($Token.accessToken)"
        $script:IotHubAccessTokenRenewUtc = if ($Token.expiresOn) { [DateTimeOffset]::FromUnixTimeSeconds([long]$Token.expiresOn).UtcDateTime.AddMinutes(-3) }
            else { [DateTime]::UtcNow.AddMinutes(1) }
    }
    return $script:IotHubAccessToken
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
