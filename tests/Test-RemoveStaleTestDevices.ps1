<#
.SYNOPSIS
Drives Remove-AzIotStaleTestDevices with `az` and the service API stubbed, and checks which devices
it deletes from the hub and the DPS, which it keeps and why, and that it never deletes from the hub
a device whose DPS registration it could not delete.

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
    }
}

function global:az {
    $Argv = @($args | %{ $_ } | %{ "$_" })
    $Joined = $Argv -join ' '
    $global:Stub.Calls.Add(@{ Line = $Joined })
    $global:LASTEXITCODE = 0
    switch -Regex ($Joined) {
        '^resource show .*--resource-type Microsoft.Devices/IotHubs' { return '{"hostName":"stubhub.azure-devices.net","iotHubDetails":{"gatewayVersion":"V1"}}' }
        '^account get-access-token --resource https://iothubs.azure.net' {
            $global:Stub.TokenRequests++
            return (ConvertTo-Json @{ accessToken = 'stub-token'; expiresOn = [DateTimeOffset]::UtcNow.AddSeconds($global:Stub.TokenLifetimeSeconds).ToUnixTimeSeconds() })
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
                    @{ deviceId = 'ci-3-gone'; errorCode = 'DeviceNotFound'; errorStatus = 'gone' }
                    @{ deviceId = 'ci-4-bulk-error'; errorCode = 'ThrottleBacklogLimitExceeded'; errorStatus = 'busy' }
                ) | ?{ $_.deviceId -in @($Call.Body | %{ $_.id }) }
                return @{ Status = $(if ($Errors) { 400 } else { 200 }); Text = (ConvertTo-Json -Depth 5 -InputObject @{ isSuccessful = -not $Errors; errors = @($Errors) }) }
            }
            '^DELETE https://stubhub\.azure-devices\.net/devices/([^?]+)\?' { return @{ Status = 204; Text = '' } }
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
& $Module { $script:IotHubAccessToken = $null }
try { Remove-AzIotStaleTestDevices @Common -Confirm:$false | Out-Null } catch { }
Assert ($Stub.TokenRequests -gt 1) "token: a token about to expire must not be reused; got $($Stub.TokenRequests) request(s)."
Reset-Stub
& $Module { $script:IotHubAccessToken = $null }
try { Remove-AzIotStaleTestDevices @Common -Confirm:$false | Out-Null } catch { }
Assert ($Stub.TokenRequests -eq 1) "token: a valid token must be reused; got $($Stub.TokenRequests) request(s)."

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
