<#
.SYNOPSIS
Drives Remove-AzIotStaleTestDevices with `az` and the service APIs stubbed, and checks which devices
it deletes from the hub, the DPS and ADR, which it keeps and why, and that it never deletes from the
hub a device whose DPS registration or ADR device it could not delete.

.DESCRIPTION
Deletes nothing and needs no credentials.

.EXAMPLE
pwsh -NoProfile -File tests/Test-RemoveStaleTestDevices.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $RepoRoot 'scripts/AzIotSdkTest/AzIotSdkTest.psd1') -Force
$Module = Get-Module AzIotSdkTest
& $Module { function script:Start-Sleep { } }

$Old = (Get-Date).ToUniversalTime().AddDays(-2).ToString('o')
$Recent = (Get-Date).ToUniversalTime().AddMinutes(-30).ToString('o')
$Never = '0001-01-01T00:00:00Z'
function New-Twin([string]$Id, [string]$Activity = $Never, [string]$TwinUpdate = $null, [string]$State = 'Disconnected') {
    $Desired = @{ '$metadata' = @{} }
    if ($TwinUpdate) { $Desired['$metadata']['$lastUpdated'] = $TwinUpdate }
    @{ deviceId = $Id; connectionState = $State; lastActivityTime = $Activity; statusUpdateTime = $Never; properties = @{ desired = $Desired; reported = @{ '$metadata' = @{} } } }
}

function Reset-Stub {
    $global:Stub = @{
        Calls = New-Object System.Collections.Generic.List[object]
        Twins = @(
            New-Twin 'ci-1-old' -Activity $Old
            New-Twin 'ci-2-twin-only' -TwinUpdate $Old
            New-Twin 'ci-3-gone' -Activity $Old
            New-Twin 'ci-4-bulk-error' -Activity $Old
            New-Twin 'ci-5-no-dps' -Activity $Old
            New-Twin 'ci-6-dps-fails' -Activity $Old
            New-Twin 'ci-7-connected' -Activity $Old -State 'Connected'
            New-Twin 'ci-8-recent' -Activity $Old -TwinUpdate $Recent
            New-Twin 'ci-9-no-time'
            New-Twin 'ci-10-pinned' -Activity $Old
            New-Twin 'other-old' -Activity $Old
        )
        PageSize = 4
        NetworkErrors = @()
        TokenRequests = 0
        TokenLifetimeSeconds = 3600
        HubGone = @('ci-3-gone')
        HubUntagged = @()
        Namespaces = @()
        NamespaceListStatus = 200
        AdrDevices = @{}
        AdrDeleteStatus = @{}
        AdrStuck = @()
        AdrDeleting = @{}
    }
}

$HubId = '/subscriptions/sub-1/resourceGroups/StubRg/providers/Microsoft.Devices/IotHubs/stubhub'
function New-Namespace([string]$Name, [string]$HubResourceId) {
    @{ id = "/subscriptions/sub-1/resourceGroups/AdrRg/providers/Microsoft.DeviceRegistry/namespaces/$Name"; name = $Name
       properties = @{ messaging = @{ endpoints = @{ 'hub-1' = @{ resourceId = $HubResourceId } } } } }
}
function New-AdrDevice([string]$Namespace, [string]$Name, [string]$ExternalId = $Name, [string]$Changed = $Old) {
    @{ id = "/subscriptions/sub-1/resourceGroups/AdrRg/providers/Microsoft.DeviceRegistry/namespaces/$Namespace/registryDevices/$Name"; name = $Name
       properties = @{ externalDeviceId = $ExternalId }; systemData = @{ createdAt = $Old; lastModifiedAt = $Changed } }
}

function global:az {
    $Argv = @($args | %{ $_ } | %{ "$_" })
    $Joined = $Argv -join ' '
    $global:Stub.Calls.Add(@{ Line = $Joined })
    $global:LASTEXITCODE = 0
    switch -Regex ($Joined) {
        '^resource show .*--resource-type Microsoft.Devices/IotHubs' { return "{`"id`":`"$HubId`",`"name`":`"stubhub`",`"properties`":{`"hostName`":`"stubhub.azure-devices.net`",`"iotHubDetails`":{`"gatewayVersion`":`"V1`"}}}" }
        '^account get-access-token --resource (\S+)' {
            $Resource = $Matches[1]
            if ($Resource -like '*iothubs*') { $global:Stub.TokenRequests++ }
            $Token = if ($Resource -like '*management*') { 'arm-token' } else { 'stub-token' }
            return (ConvertTo-Json @{ accessToken = $Token; expiresOn = [DateTimeOffset]::UtcNow.AddSeconds($global:Stub.TokenLifetimeSeconds).ToUnixTimeSeconds() })
        }
        '^iot dps connection-string show' { return 'HostName=stubdps.azure-devices-provisioning.net;SharedAccessKeyName=provisioningserviceowner;SharedAccessKey=RkFLRQ==' }
    }
    Write-Error -ErrorAction Continue "unexpected az call: $Joined"
    $global:LASTEXITCODE = 1
}

& $Module {
    function script:Send-ServiceHttpRequest([string]$Method, [string]$Uri, [Hashtable]$Headers, [string]$Content) {
        $Call = @{ Line = "$Method $Uri"; Headers = $Headers.Clone(); Body = $(if ($Content) { ConvertFrom-Json -InputObject $Content }) }
        $global:Stub.Calls.Add($Call)
        if (@($global:Stub.NetworkErrors | ?{ "$Method $Uri" -match $_ }).Count -gt 0) { return @{ Status = 0; Text = 'stub network error' } }
        switch -Regex ("$Method $Uri") {
            '^POST https://stubhub\.azure-devices\.net/devices/query\?' {
                $Start = if ($Headers['x-ms-continuation']) { [int]$Headers['x-ms-continuation'] } else { 0 }
                $Page = @($global:Stub.Twins | Select-Object -Skip $Start -First $global:Stub.PageSize)
                $Next = if ($Start + $global:Stub.PageSize -lt $global:Stub.Twins.Count) { "$($Start + $global:Stub.PageSize)" }
                return @{ Status = 200; Text = (ConvertTo-Json -Depth 10 -InputObject $Page); Continuation = $Next }
            }
            '^DELETE https://stubdps\.azure-devices-provisioning\.net/registrations/([^?]+)\?' {
                switch ($Matches[1]) {
                    'ci-5-no-dps' { return @{ Status = 404; Text = '{"errorCode":404203}' } }
                    'ci-6-dps-fails' { return @{ Status = 500; Text = '{"errorCode":500000}' } }
                }
                return @{ Status = 204; Text = '' }
            }
            '^POST https://stubhub\.azure-devices\.net/devices\?' {
                $Errors = @(
                    $global:Stub.HubGone | %{ @{ deviceId = $_; errorCode = 'DeviceNotFound'; errorStatus = 'gone' } }
                    @{ deviceId = 'ci-4-bulk-error'; errorCode = 'ThrottleBacklogLimitExceeded'; errorStatus = 'busy' }
                ) | ?{ $_.deviceId -in @($Call.Body | %{ $_.id }) }
                return @{ Status = $(if ($Errors) { 400 } else { 200 }); Text = (ConvertTo-Json -Depth 5 -InputObject @{ isSuccessful = -not $Errors; errors = @($Errors) }) }
            }
            '^DELETE https://stubhub\.azure-devices\.net/devices/([^?]+)\?' { return @{ Status = 204; Text = '' } }
            '^GET https://stubhub\.azure-devices\.net/devices/([^?]+)\?' {
                if ($Matches[1] -in $global:Stub.HubUntagged) { return @{ Status = 200; Text = '{}' } }
                return @{ Status = 404; Text = '{"errorCode":404001}' }
            }
            '^GET https://management\.azure\.com/subscriptions/sub-1/providers/Microsoft\.DeviceRegistry/namespaces\?(.*)$' {
                if ($global:Stub.NamespaceListStatus -ne 200) {
                    $Code = if ($global:Stub.NamespaceListStatus -eq 409) { 'MissingSubscriptionRegistration' } else { 'AuthorizationFailed' }
                    return @{ Status = $global:Stub.NamespaceListStatus; Text = "{`"error`":{`"code`":`"$Code`"}}" }
                }
                # One namespace per page.
                $Index = if ($Matches[1] -match 'page=(\d+)') { [int]$Matches[1] } else { 0 }
                $Page = @{ value = @($global:Stub.Namespaces | Select-Object -Skip $Index -First 1) }
                if ($Index + 1 -lt $global:Stub.Namespaces.Count) { $Page.nextLink = "https://management.azure.com/subscriptions/sub-1/providers/Microsoft.DeviceRegistry/namespaces?page=$($Index + 1)" }
                return @{ Status = 200; Text = (ConvertTo-Json -Depth 10 -InputObject $Page) }
            }
            '^GET https://management\.azure\.com(/subscriptions/.+/namespaces/[^/]+)/registryDevices\?(.*)$' {
                $NamespaceId = $Matches[1]
                $Query = $Matches[2]
                $Listed = @(@($global:Stub.AdrDevices[$NamespaceId]) | ?{ $_ } | ?{
                    $Name = $_.name
                    if ($Name -in $global:Stub.AdrStuck) { return $true }
                    -not $global:Stub.AdrDeleting.ContainsKey($Name)
                })
                # Two devices per page.
                $Index = if ($Query -match 'page=(\d+)') { [int]$Matches[1] } else { 0 }
                $Page = @{ value = @($Listed | Select-Object -Skip $Index -First 2) }
                if ($Index + 2 -lt $Listed.Count) { $Page.nextLink = "https://management.azure.com$NamespaceId/registryDevices?page=$($Index + 2)" }
                return @{ Status = 200; Text = (ConvertTo-Json -Depth 10 -InputObject $Page) }
            }
            '^DELETE https://management\.azure\.com/.+/registryDevices/([^?]+)\?' {
                $Name = $Matches[1]
                $Status = if ($global:Stub.AdrDeleteStatus.ContainsKey($Name)) { $global:Stub.AdrDeleteStatus[$Name] } else { 202 }
                # An accepted delete has completed by the next listing, unless the device is stuck.
                if ($Status -in 200, 202, 204) { $global:Stub.AdrDeleting[$Name] = $true }
                return @{ Status = $Status; Text = $(if ($Status -ge 400) { '{"error":{"code":"Boom"}}' } else { '' }) }
            }
        }
        return @{ Status = 418; Text = "unexpected request: $Method $Uri" }
    }
}

$Problems = New-Object System.Collections.Generic.List[string]
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { $Problems.Add($Message) } }
# The unary comma keeps a single match an array.
function Find-Calls([string]$Pattern) { , @($Stub.Calls | ?{ $_.Line -match $Pattern }) }
function Get-Ids([object[]]$Calls, [string]$Pattern) { @($Calls | %{ [regex]::Match($_.Line, $Pattern).Groups[1].Value } | Sort-Object -Unique) -join ',' }

$Common = @{ ResourceGroup = 'StubRg'; IotHubName = 'stubhub'; DpsName = 'stubdps'; DeviceIdPattern = '^ci-'; ExcludeDeviceIds = @('ci-10-pinned') }

# A run: every page queried, stale devices deleted from the DPS then the hub, the rest kept.
Reset-Stub
$Thrown = $null
$Result = $null
try { $Result = Remove-AzIotStaleTestDevices @Common -Confirm:$false } catch { $Thrown = $_.Exception.Message }
Assert ("$Thrown" -match '1 stale test device\(s\) could not be deleted: ci-6-dps-fails') "run: expected a failure naming ci-6-dps-fails; got '$Thrown'."
Assert ((Find-Calls 'devices/query').Count -eq 3) "run: expected 3 query pages, got $((Find-Calls 'devices/query').Count)."
Assert ((Find-Calls 'devices/query')[0].Body.query -eq 'SELECT * FROM devices') "run: unexpected query '$((Find-Calls 'devices/query')[0].Body.query)'."
Assert (((Find-Calls 'devices/query')[0].Headers.Authorization) -eq 'Bearer stub-token') "run: the hub must be called with Microsoft Entra ID."
$Expected = 'ci-1-old,ci-2-twin-only,ci-3-gone,ci-4-bulk-error,ci-5-no-dps,ci-6-dps-fails'
$DpsDeleted = Get-Ids (Find-Calls '^DELETE https://stubdps') '/registrations/([^?]+)\?'
Assert ($DpsDeleted -eq $Expected) "run: DPS deletes were '$DpsDeleted', expected '$Expected'."
Assert ((Find-Calls '^DELETE https://stubdps')[0].Headers.Authorization -like 'SharedAccessSignature sr=stubdps.azure-devices-provisioning.net*') "run: the DPS must be called with its key."
$Bulk = Find-Calls '^POST https://stubhub\.azure-devices\.net/devices\?'
$BulkIds = @($Bulk.Body | %{ $_.id } | Sort-Object) -join ','
Assert ($Bulk.Count -eq 1 -and $BulkIds -eq 'ci-1-old,ci-2-twin-only,ci-3-gone,ci-4-bulk-error,ci-5-no-dps' -and @($Bulk.Body | ?{ $_.importMode -ne 'delete' }).Count -eq 0) "run: bulk delete of '$BulkIds'; a device whose DPS registration failed must stay on the hub."
$Single = Find-Calls '^DELETE https://stubhub'
Assert ((Get-Ids $Single '/devices/([^?]+)\?') -eq 'ci-4-bulk-error' -and $Single[0].Headers['If-Match'] -eq '"*"') "run: only the device the bulk delete failed must be deleted on its own, with If-Match: *."

# The same run without the failing device reports what happened to each one.
Reset-Stub
$Stub.Twins = @($Stub.Twins | ?{ $_.deviceId -ne 'ci-6-dps-fails' })
$Result = Remove-AzIotStaleTestDevices @Common -Confirm:$false
$ByDevice = @{}
$Result | %{ $ByDevice[$_.DeviceId] = $_.Result }
$ExpectedResults = [ordered]@{
    'ci-1-old' = 'Deleted'; 'ci-2-twin-only' = 'Deleted'; 'ci-3-gone' = 'AlreadyDeleted'; 'ci-4-bulk-error' = 'Deleted'; 'ci-5-no-dps' = 'Deleted'
    'ci-7-connected' = 'Kept: connected'; 'ci-8-recent' = 'Kept: active within 6 h'; 'ci-9-no-time' = 'Kept: no activity time'; 'ci-10-pinned' = 'Kept: excluded'
}
foreach ($Id in $ExpectedResults.Keys) {
    Assert ($ByDevice[$Id] -eq $ExpectedResults[$Id]) "results: $Id is '$($ByDevice[$Id])', expected '$($ExpectedResults[$Id])'."
}
Assert (-not $ByDevice.ContainsKey('other-old')) "results: a device not matching -DeviceIdPattern must not be selected."

# -WhatIf deletes nothing.
Reset-Stub
$Result = Remove-AzIotStaleTestDevices @Common -WhatIf
Assert ((Find-Calls '^(DELETE|POST https://stubhub\.azure-devices\.net/devices\?)').Count -eq 0) "whatif: nothing must be deleted."
Assert (@($Result | ?{ $_.Result -eq 'WhatIf' }).Count -eq 6) "whatif: expected 6 devices reported WhatIf, got $(@($Result | ?{ $_.Result -eq 'WhatIf' }).Count)."

# -TwinTags selects on the hub, quoting values; no DPS when none is given.
Reset-Stub
$Stub.Twins = @()
Remove-AzIotStaleTestDevices -ResourceGroup StubRg -IotHubName stubhub -TwinTags @{ e2eSuite = 'horton'; 'owner.name' = "o'k" } -Confirm:$false | Out-Null
$Query = (Find-Calls 'devices/query')[0].Body.query
Assert ($Query -eq "SELECT * FROM devices WHERE tags.e2eSuite = 'horton' AND tags.owner.name = 'o''k'") "tags: unexpected query '$Query'."
Assert ((Find-Calls 'dps').Count -eq 0) "tags: no DPS must be called without -DpsName."

# A network error, once retries are exhausted, fails its device and the run goes on with the rest.
Reset-Stub
$Stub.Twins = @(New-Twin 'ci-1-old' -Activity $Old; New-Twin 'ci-2-twin-only' -TwinUpdate $Old; New-Twin 'ci-3-gone' -Activity $Old)
$Stub.NetworkErrors = @('^DELETE https://stubdps.*/registrations/ci-1-old\?', '^POST https://stubhub\.azure-devices\.net/devices\?')
$Thrown = $null
try { Remove-AzIotStaleTestDevices @Common -Confirm:$false | Out-Null } catch { $Thrown = $_.Exception.Message }
Assert ("$Thrown" -match '1 stale test device\(s\) could not be deleted: ci-1-old\.') "network: expected a failure naming only ci-1-old; got '$Thrown'."
Assert ((Find-Calls 'registrations/ci-1-old').Count -eq 6) "network: expected 6 attempts on the DPS, got $((Find-Calls 'registrations/ci-1-old').Count)."
$Single = Get-Ids (Find-Calls '^DELETE https://stubhub') '/devices/([^?]+)\?'
Assert ($Single -eq 'ci-2-twin-only,ci-3-gone') "network: after a failed bulk delete, expected single deletes of the rest; got '$Single'."

# A token is renewed before it expires.
Reset-Stub
$Stub.TokenLifetimeSeconds = 60
& $Module { $script:EntraAccessTokens = $null }
try { Remove-AzIotStaleTestDevices @Common -Confirm:$false | Out-Null } catch { }
Assert ($Stub.TokenRequests -gt 1) "token: a token about to expire must not be reused; got $($Stub.TokenRequests) request(s)."
Reset-Stub
& $Module { $script:EntraAccessTokens = $null }
try { Remove-AzIotStaleTestDevices @Common -Confirm:$false | Out-Null } catch { }
Assert ($Stub.TokenRequests -eq 1) "token: a valid token must be reused; got $($Stub.TokenRequests) request(s)."

# ADR: devices of the namespaces linked to the hub deleted after the DPS and before the hub, and
# ADR devices whose hub device is gone deleted too.
Reset-Stub
& $Module { $script:AdrDeviceDeleteTimeoutSeconds = 0 }
$Ns = (New-Namespace 'ns-linked' $HubId.ToUpperInvariant()).id
$Stub.Namespaces = @(
    New-Namespace 'ns-other' '/subscriptions/sub-1/resourceGroups/StubRg/providers/Microsoft.Devices/IotHubs/otherhub'
    New-Namespace 'ns-linked' $HubId.ToUpperInvariant()
)
$Stub.Twins = @(
    New-Twin 'ci-1-old' -Activity $Old
    New-Twin 'ci-2-name-only' -Activity $Old
    New-Twin 'ci-3-adr-fails' -Activity $Old
    New-Twin 'ci-4-adr-stuck' -Activity $Old
    New-Twin 'ci-5-recent' -Activity $Recent
)
$Stub.AdrDevices[$Ns] = @(
    New-AdrDevice 'ns-linked' 'ci-1-old'
    New-AdrDevice 'ns-linked' 'ci-2-name-only' -ExternalId ''
    New-AdrDevice 'ns-linked' 'ci-3-adr-fails'
    New-AdrDevice 'ns-linked' 'ci-4-adr-stuck'
    New-AdrDevice 'ns-linked' 'ci-5-recent'
    New-AdrDevice 'ns-linked' 'adr-20' -ExternalId 'ci-20-orphan'
    New-AdrDevice 'ns-linked' 'ci-21-orphan-recent' -Changed $Recent
    New-AdrDevice 'ns-linked' 'ci-22-untagged'
    New-AdrDevice 'ns-linked' 'other-adr'
)
$Stub.AdrDevices[(New-Namespace 'ns-other' '').id] = @(New-AdrDevice 'ns-other' 'ci-30-elsewhere')
$Stub.AdrDeleteStatus = @{ 'ci-2-name-only' = 204; 'ci-3-adr-fails' = 500 }
$Stub.AdrStuck = @('ci-4-adr-stuck')
$Stub.HubGone = @('ci-2-name-only')
$Stub.HubUntagged = @('ci-22-untagged')
$Thrown = $null
$Result = $null
try { $Result = Remove-AzIotStaleTestDevices @Common -Confirm:$false } catch { $Thrown = $_.Exception.Message }
& $Module { $script:AdrDeviceDeleteTimeoutSeconds = 900 }
Assert ("$Thrown" -match '2 stale test device\(s\) could not be deleted: ci-3-adr-fails, ci-4-adr-stuck') "adr: expected a failure naming ci-3-adr-fails and ci-4-adr-stuck; got '$Thrown'."
Assert ((Find-Calls 'ns-other/registryDevices').Count -eq 0) "adr: a namespace not linked to the hub must not be listed."
Assert (@($Stub.Calls | ?{ $_.Line -match '^\w+ https://management' -and $_.Headers.Authorization -ne 'Bearer arm-token' }).Count -eq 0) "adr: ARM must be called with Microsoft Entra ID."
$AdrDeletes = Find-Calls '^DELETE https://management'
$AdrDeleted = Get-Ids $AdrDeletes '/registryDevices/([^?]+)\?'
Assert ($AdrDeleted -eq 'adr-20,ci-1-old,ci-2-name-only,ci-3-adr-fails,ci-4-adr-stuck') "adr: ADR deletes were '$AdrDeleted'."
$HubReads = Get-Ids (Find-Calls '^GET https://stubhub') '/devices/([^?]+)\?'
Assert ($HubReads -eq 'ci-20-orphan,ci-21-orphan-recent,ci-22-untagged') "adr: hub reads were '$HubReads'; only pattern-matching ADR devices not queried must be read."
$DpsDeleted = Get-Ids (Find-Calls '^DELETE https://stubdps') '/registrations/([^?]+)\?'
Assert ($DpsDeleted -eq 'ci-1-old,ci-2-name-only,ci-20-orphan,ci-3-adr-fails,ci-4-adr-stuck') "adr: DPS deletes were '$DpsDeleted'."
$BulkIds = @((Find-Calls '^POST https://stubhub\.azure-devices\.net/devices\?').Body | %{ $_.id } | Sort-Object) -join ','
Assert ($BulkIds -eq 'ci-1-old,ci-2-name-only') "adr: hub deletes were '$BulkIds'; a device whose ADR device was not deleted must stay on the hub."
$Lines = @($Stub.Calls | %{ $_.Line })
$LastDps = [Array]::FindLastIndex([string[]]$Lines, [Predicate[string]]{ param($l) $l -match '^DELETE https://stubdps' })
$FirstAdr = [Array]::FindIndex([string[]]$Lines, [Predicate[string]]{ param($l) $l -match '^DELETE https://management' })
$LastAdrList = [Array]::FindLastIndex([string[]]$Lines, [Predicate[string]]{ param($l) $l -match 'registryDevices\?' })
$FirstHub = [Array]::FindIndex([string[]]$Lines, [Predicate[string]]{ param($l) $l -match '^POST https://stubhub\.azure-devices\.net/devices\?' })
Assert ($LastDps -lt $FirstAdr -and $LastAdrList -lt $FirstHub) "adr: expected DPS, then ADR, then hub deletes."

Reset-Stub
& $Module { $script:AdrDeviceDeleteTimeoutSeconds = 0 }
$Stub.Namespaces = @(New-Namespace 'ns-linked' $HubId)
$Stub.Twins = @(New-Twin 'ci-1-old' -Activity $Old; New-Twin 'ci-2-name-only' -Activity $Old)
$Stub.AdrDevices[$Ns] = @(New-AdrDevice 'ns-linked' 'ci-1-old'; New-AdrDevice 'ns-linked' 'ci-2-name-only' -ExternalId ''; New-AdrDevice 'ns-linked' 'adr-20' -ExternalId 'ci-20-orphan'; New-AdrDevice 'ns-linked' 'ci-21-orphan-recent' -Changed $Recent)
$Stub.HubGone = @('ci-2-name-only')
$Result = Remove-AzIotStaleTestDevices @Common -Confirm:$false
& $Module { $script:AdrDeviceDeleteTimeoutSeconds = 900 }
$ByDevice = @{}
$Result | %{ $ByDevice[$_.DeviceId] = $_ }
foreach ($Expected in @(
    @('ci-1-old', 'Deleted', $true, 1), @('ci-2-name-only', 'Deleted', $true, 1)
    @('ci-20-orphan', 'Deleted', $false, 1), @('ci-21-orphan-recent', 'Kept: active within 6 h', $false, 1)
)) {
    $Device = $ByDevice[$Expected[0]]
    Assert ($null -ne $Device -and $Device.Result -eq $Expected[1] -and $Device.OnHub -eq $Expected[2] -and @($Device.AdrDeviceIds).Count -eq $Expected[3]) "adr results: $($Expected[0]) is '$($Device.Result)' (OnHub $($Device.OnHub), $(@($Device.AdrDeviceIds).Count) ADR device(s)), expected '$($Expected[1])'."
}

# Without -DeviceIdPattern, ADR devices are only those of the hub devices queried.
Reset-Stub
$Stub.Namespaces = @(New-Namespace 'ns-linked' $HubId)
$Stub.Twins = @()
$Stub.AdrDevices[$Ns] = @(New-AdrDevice 'ns-linked' 'ci-20-orphan')
Remove-AzIotStaleTestDevices -ResourceGroup StubRg -IotHubName stubhub -TwinTags @{ e2eSuite = 'horton' } -Confirm:$false | Out-Null
Assert ((Find-Calls '^(GET https://stubhub|DELETE)').Count -eq 0) "adr tags: an ADR device must not be selected without -DeviceIdPattern."

# ADR not registered on the subscription: no ADR. Any other failure to list namespaces: nothing deleted.
foreach ($Case in @(@{ Status = 409; Throws = $false }, @{ Status = 403; Throws = $true })) {
    Reset-Stub
    $Stub.NamespaceListStatus = $Case.Status
    $Thrown = $null
    try { Remove-AzIotStaleTestDevices @Common -Confirm:$false 2>$null | Out-Null } catch { $Thrown = $_.Exception.Message }
    if ($Case.Throws) {
        Assert ("$Thrown" -match 'ADR namespaces' -and (Find-Calls '^(DELETE|POST https://stubhub\.azure-devices\.net/devices\?)').Count -eq 0) "adr $($Case.Status): expected a failure before any delete; got '$Thrown'."
    } else {
        Assert ("$Thrown" -match 'ci-6-dps-fails' -and (Find-Calls '^POST https://stubhub\.azure-devices\.net/devices\?').Count -eq 1) "adr $($Case.Status): expected the run to go on without ADR; got '$Thrown'."
    }
}

# Refusals before anything is called.
foreach ($Case in @(
    @{ Name = 'no selection'; Arguments = @{}; Pattern = 'DeviceIdPattern' }
    @{ Name = 'bad tag'; Arguments = @{ TwinTags = @{ "x' OR 1=1 --" = 'y' } }; Pattern = 'not a name' }
)) {
    Reset-Stub
    $Thrown = $null
    $Arguments = $Case.Arguments
    try { Remove-AzIotStaleTestDevices -ResourceGroup StubRg -IotHubName stubhub @Arguments -Confirm:$false | Out-Null } catch { $Thrown = $_.Exception.Message }
    Assert ("$Thrown" -match $Case.Pattern -and $Stub.Calls.Count -eq 0) "$($Case.Name): expected a refusal before any request; got '$Thrown'."
}

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: stale test devices."
exit 0
