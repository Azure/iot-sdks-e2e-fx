<#
.SYNOPSIS
Drives New-AzIotMqttv5TestEnvironment with `az` stubbed, and checks the MQTT v5 hub and DPS it
creates, that it never calls 'az iot hub', that a topic group dropped by the ADR link is restored,
that telemetry routing to an Event Hub goes through one ARM write, and the environment it returns.

.DESCRIPTION
Provisions nothing and needs no credentials. `az` is replaced by a stub that records every call and
keeps each ARM resource written through 'az rest', so later reads see earlier writes, as a full-body
PUT would leave them.

.EXAMPLE
pwsh -NoProfile -File tests/Test-Mqttv5Provisioning.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $RepoRoot 'scripts/AzIotSdkTest/AzIotSdkTest.psd1') -Force
$Module = Get-Module AzIotSdkTest
# ADR and RBAC plumbing is out of scope here. The link is a full write of the hub, so the stub can
# drop the hub's topic groups the way that write can.
& $Module {
    function script:Start-Sleep { }
    function script:Install-AzureIotCliExtension { }
    function script:Wait-AzRoleAssignment { }
    function script:New-AdrNamespace { [pscustomobject]@{ id = '/adr'; identity = [pscustomobject]@{ principalId = 'adr-principal' } } }
    function script:New-AdrCertificateAuthority { }
    function script:Sync-DpsAdrConfiguration { }
    function script:Connect-AdrNamespace {
        param($NamespaceId, $Location, $IotHubId, $DpsId, $ExpectedPrincipalId)
        $global:Stub.Calls.Add([pscustomobject]@{ Line = '<Connect-AdrNamespace>'; Body = $null })
        if ($global:Stub.LinkDropsTopicGroups) {
            $Hub = $global:Stub.Resources[(Get-StubHubKey)]
            $Hub.properties.PSObject.Properties.Remove('mqttV5Settings')
        }
    }
}

function global:Get-StubKey([string]$Url) { ([uri]$Url).AbsolutePath.ToLowerInvariant().TrimEnd('/') }
function global:Get-StubHubKey { @($global:Stub.Resources.Keys | ?{ $_ -like '*/microsoft.devices/iothubs/*' -and $_ -notlike '*/consumergroups/*' })[0] }

function global:Reset-Stub([switch]$LinkDropsTopicGroups) {
    $global:Stub = @{
        Calls = New-Object System.Collections.Generic.List[object]
        Resources = @{}
        RoleAssignments = @()
        EventHubs = @()
        LinkDropsTopicGroups = [bool]$LinkDropsTopicGroups
    }
}

function global:az {
    $Argv = @($args | %{ "$_" })
    $Joined = $Argv -join ' '
    $Body = $null
    $BodyIndex = [array]::IndexOf($Argv, '--body')
    if ($BodyIndex -ge 0 -and $Argv[$BodyIndex + 1].StartsWith('@')) {
        $Body = Get-Content -Raw -Path $Argv[$BodyIndex + 1].Substring(1)
    }
    $global:Stub.Calls.Add([pscustomobject]@{ Line = $Joined; Body = $Body })
    $global:LASTEXITCODE = 0
    function Opt([string]$Name) { $i = [array]::IndexOf($Argv, $Name); if ($i -ge 0) { $Argv[$i + 1] } }

    switch -Regex ($Joined) {
        '^account show --query id -o tsv' { return '00000000-0000-0000-0000-000000000000' }
        '^account show' { return '{"id":"00000000-0000-0000-0000-000000000000","user":{"name":"stub","type":"servicePrincipal"}}' }
        '^account get-access-token' { return "e30.$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"oid":"caller-oid"}')).TrimEnd('=')).sig" }
        '^group exists' { return 'false' }
        '^rest ' {
            $Url = Opt '--url'
            $Method = Opt '--method'
            $Key = Get-StubKey $Url
            if ($Method -eq 'POST' -and $Key -like '*/listkeys') {
                return '{"value":[{"keyName":"service","primaryKey":"U0VSVklDRQ=="},{"keyName":"iothubowner","primaryKey":"T1dORVI="}]}'
            }
            if ($Method -eq 'PUT') {
                $Resource = $Body | ConvertFrom-Json
                $Resource | Add-Member -Force id ([uri]$Url).AbsolutePath
                if ($null -eq $Resource.properties) { $Resource | Add-Member -Force properties ([pscustomobject]@{}) }
                $Resource.properties | Add-Member -Force provisioningState 'Succeeded'
                if ($Key -like '*/provisioningservices/*') {
                    $Resource.properties | Add-Member -Force idScope '0ne00000000'
                    $Resource.properties | Add-Member -Force deviceProvisioningHostName 'global.azure-devices-provisioning.net'
                    $Resource.properties | Add-Member -Force serviceOperationsHostName 'stubdps.azure-devices-provisioning.net'
                }
                if ($Key -like '*/iothubs/*' -and $Key -notlike '*/consumergroups/*') {
                    # An MQTT v5 hub reports no hostName, and separate service and device host names.
                    $Resource.properties | Add-Member -Force state 'Active'
                    $Resource.properties | Add-Member -Force hostName ''
                    $Resource.properties | Add-Member -Force serviceHostName 'stubhub.service.azure-devices.net'
                    $Resource.properties | Add-Member -Force deviceHostName 'stubhub.device.azure-devices.net'
                    $Resource.properties | Add-Member -Force eventHubEndpoints ([pscustomobject]@{ events = [pscustomobject]@{
                        endpoint = 'sb://ihsuprodstub.servicebus.windows.net/'; path = 'stubhub'; partitionCount = 4 } })
                }
                if ($Resource.identity) {
                    # The principal id is the identity's, not the request's: it survives a full write.
                    $Previous = $global:Stub.Resources[$Key]
                    $PrincipalId = if ($Previous -and $Previous.identity.principalId) { $Previous.identity.principalId } else { "principal-$($Key.Split('/')[-1])" }
                    $Resource.identity | Add-Member -Force principalId $PrincipalId
                }
                $global:Stub.Resources[$Key] = $Resource
                return ($Resource | ConvertTo-Json -Depth 20)
            }
            if ($Key -like '*/consumergroups') {
                $Names = @('$Default') + @($global:Stub.Resources.Keys | ?{ $_ -like "$Key/*" } | %{ $global:Stub.Resources[$_].properties.name })
                return (@{ value = @($Names | %{ @{ name = $_ } }) } | ConvertTo-Json -Depth 5)
            }
            if ($global:Stub.Resources.ContainsKey($Key)) { return ($global:Stub.Resources[$Key] | ConvertTo-Json -Depth 20) }
            return '{"id":"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/StubRg","properties":{"provisioningState":"Succeeded"}}'
        }
        '^eventhubs namespace create' { return "{`"name`":`"$(Opt '--name')`",`"serviceBusEndpoint`":`"https://$(Opt '--name').servicebus.windows.net:443/`"}" }
        '^eventhubs eventhub list' { return (ConvertTo-Json -Depth 5 -InputObject @($global:Stub.EventHubs)) }
        '^eventhubs eventhub create' {
            $EventHub = [pscustomobject]@{ name = (Opt '--name'); partitionCount = [int](Opt '--partition-count'); id = "/eh/$(Opt '--namespace-name')/$(Opt '--name')" }
            $global:Stub.EventHubs += $EventHub
            return ($EventHub | ConvertTo-Json)
        }
        '^eventhubs eventhub consumer-group list' { return '$Default' }
        '^role assignment list' { return '[]' }
        '^role assignment create' { $global:Stub.RoleAssignments += "$(Opt '--assignee-object-id')|$(Opt '--role')|$(Opt '--scope')"; return '' }
        '^iot dps connection-string show' { return 'HostName=stubdps.azure-devices-provisioning.net;SharedAccessKeyName=provisioningserviceowner;SharedAccessKey=RkFLRQ==' }
        default { return '' }
    }
}

$Problems = New-Object System.Collections.Generic.List[string]
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { $Problems.Add($Message) } }
function Find-Calls([string]$Pattern) { @(for ($i = 0; $i -lt $Stub.Calls.Count; $i++) { if ($Stub.Calls[$i].Line -match $Pattern) { $i } }) }

$HubPutPattern = '^rest --method PUT --url https://management\.azure\.com/subscriptions/[^/]+/resourceGroups/StubRg/providers/Microsoft\.Devices/IotHubs/stubhub\?'
$DpsPutPattern = '^rest --method PUT --url https://eastus2euap\.management\.azure\.com/.*/provisioningServices/stubdps\?'
$EnvArgs = @{ ResourceGroup = 'StubRg'; IotHubName = 'stubhub'; DpsName = 'stubdps' }
$IotHubDataContributor = '4fc6c259-987e-4a07-842e-c321cc9d413f'

# Everything on: local auth disabled, telemetry to an Event Hub, and a link that drops the topic groups.
Reset-Stub -LinkDropsTopicGroups
$Info = New-AzIotMqttv5TestEnvironment @EnvArgs -DisableLocalAuth -EventHubConsumerGroups e2e-0 -RouteTelemetryToEventHub -TelemetryEventHubConsumerGroups t-0
$HubPuts = Find-Calls $HubPutPattern
$DpsPut = @(Find-Calls $DpsPutPattern)
$Link = @(Find-Calls '^<Connect-AdrNamespace>')
Assert ($DpsPut.Count -eq 1 -and $HubPuts.Count -ge 1 -and $DpsPut[0] -lt $HubPuts[0]) "full: the DPS PUT ($DpsPut) must precede the first hub PUT ($($HubPuts -join ','))."
Assert (@(Find-Calls '^iot hub ').Count -eq 0) "full: 'az iot hub' must not be called: $((Find-Calls '^iot hub ' | %{ $Stub.Calls[$_].Line }) -join ' | ')"
Assert (@(Find-Calls '^rest .*/IotHubs/stubhub[/?]' | ?{ $Stub.Calls[$_].Line -notmatch 'api-version=2026-10-01-preview' }).Count -eq 0) "full: every hub call must use api-version 2026-10-01-preview."
if ($HubPuts.Count -ge 1) {
    $Create = $Stub.Calls[$HubPuts[0]].Body | ConvertFrom-Json
    $Route = @($Create.properties.routing.routes)
    $Group = @($Create.properties.mqttV5Settings.topicGroups)
    Assert ($Create.sku.name -eq 'S1' -and $Create.identity.type -eq 'SystemAssigned' -and $Create.location -eq 'eastus2euap') "full: hub create body has sku '$($Create.sku.name)', identity '$($Create.identity.type)', location '$($Create.location)'."
    Assert ($Create.properties.connectionProfile -eq 'MqttV5' -and $Create.properties.disableLocalAuth -eq $true -and $Create.properties.minTlsVersion -eq '1.2') "full: hub create body: $($Stub.Calls[$HubPuts[0]].Body)"
    Assert ($Route.Count -eq 1 -and $Route[0].name -eq 'builtin-events' -and (@($Route[0].endpointNames) -join ',') -eq 'events' -and $Route[0].isEnabled -eq $true -and $Route[0].condition -eq 'true') "full: hub create body must route device messages to the built-in endpoint."
    Assert ($Group.Count -eq 1 -and $Group[0].topicGroupId -eq 'e2e' -and (@($Group[0].topicTemplates) -join ',') -eq 'e2e/{deviceId}/#,e2e/shared/#') "full: hub create body topic groups: $($Create.properties.mqttV5Settings | ConvertTo-Json -Compress -Depth 5)"
}
Assert ($Stub.RoleAssignments -contains "caller-oid|$IotHubDataContributor|/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/StubRg/providers/Microsoft.Devices/IotHubs/stubhub") "full: the caller must be granted IoT Hub Data Contributor on the hub."
Assert ($Link.Count -eq 1 -and $Link[0] -gt $HubPuts[0]) "full: the ADR link must follow the hub create."
Assert (@(Find-Calls '^rest --method PUT .*/eventHubEndpoints/events/ConsumerGroups/e2e-0\?api-version=2026-10-01-preview').Count -eq 1) "full: consumer group e2e-0 must be created through ARM."

# After the link: one write adds the telemetry endpoint and route, and one restores the topic groups.
$AfterLink = @($HubPuts | ?{ $_ -gt $Link[0] })
Assert ($AfterLink.Count -eq 2) "full: expected 2 hub PUTs after the link (telemetry, topic groups), got $($AfterLink.Count)."
if ($AfterLink.Count -eq 2) {
    $Telemetry = $Stub.Calls[$AfterLink[0]].Body
    $Restore = $Stub.Calls[$AfterLink[1]].Body
    # Raw JSON: a one-item list must still be a list when the hub read back is written again.
    Assert ($Telemetry -match '"eventHubs":\[\{' -and $Telemetry -match '"routes":\[\{' -and $Telemetry -match '"endpointNames":\["events"\]') "full: telemetry PUT body lost a list: $Telemetry"
    Assert ($Restore -match '"topicGroups":\[\{' -and $Restore -match '"topicTemplates":\["e2e/\{deviceId\}/#","e2e/shared/#"\]') "full: topic group PUT body: $Restore"
    $TelemetryHub = $Telemetry | ConvertFrom-Json
    $Endpoint = @($TelemetryHub.properties.routing.endpoints.eventHubs)
    Assert ($Endpoint.Count -eq 1 -and $Endpoint[0].name -eq 'telemetry' -and $Endpoint[0].authenticationType -eq 'identityBased' -and $Endpoint[0].endpointUri -match '^sb://ehns-.*\.servicebus\.windows\.net$' -and $Endpoint[0].entityPath -eq 'telemetry') "full: telemetry endpoint: $($Endpoint | ConvertTo-Json -Compress)"
    Assert ((@($TelemetryHub.properties.routing.routes | %{ $_.name }) -join ',') -eq 'builtin-events,telemetry') "full: routes after the telemetry PUT are '$(@($TelemetryHub.properties.routing.routes | %{ $_.name }) -join ',')'."
    Assert ($TelemetryHub.properties.connectionProfile -eq 'MqttV5' -and $null -eq $TelemetryHub.identity.principalId -and $TelemetryHub.identity.type -eq 'SystemAssigned') "full: telemetry PUT must keep the hub's settings and send the identity by type only."
}
$Hub = $Stub.Resources[(Get-StubHubKey)]
Assert ((@($Hub.properties.mqttV5Settings.topicGroups | %{ $_.topicGroupId }) -join ',') -eq 'e2e' -and (@($Hub.properties.routing.routes | %{ $_.name }) -join ',') -eq 'builtin-events,telemetry') "full: final hub lost its topic group or routes."

Assert ($Info.IotHub.ConnectionProfile -eq 'MqttV5' -and $Info.IotHub.ServiceFqdn -eq 'stubhub.service.azure-devices.net' -and $Info.IotHub.DeviceFqdn -eq 'stubhub.device.azure-devices.net' -and $Info.IotHub.LocalAuthDisabled) "full: hub info: $($Info.IotHub.ToHashtable() | ConvertTo-Json -Compress -Depth 3)"
Assert ($Info.IotHub.ConnectionString -eq 'HostName=stubhub.service.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=T1dORVI=') "full: hub connection string is '$($Info.IotHub.ConnectionString)'."
Assert ($Info.IotHub.EventHub.ConnectionString -eq 'Endpoint=sb://ihsuprodstub.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=T1dORVI=;EntityPath=stubhub') "full: built-in endpoint connection string is '$($Info.IotHub.EventHub.ConnectionString)'."
Assert ((@($Info.IotHub.EventHub.ConsumerGroups) -join ',') -eq '$Default,e2e-0' -and $Info.IotHub.EventHub.CompatibleName -eq 'stubhub' -and $Info.IotHub.EventHub.PartitionCount -eq 4) "full: built-in endpoint info: $($Info.IotHub.EventHub.ToHashtable() | ConvertTo-Json -Compress)"
Assert ($null -ne $Info.IotHub.TelemetryEventHub -and (@($Info.IotHub.TelemetryEventHub.ConsumerGroups) -join ',') -eq '$Default,t-0') "full: telemetry Event Hub info missing or wrong."
Assert ($Info.Dps.IdScope -eq '0ne00000000' -and $Info.Dps.ServiceFqdn -eq 'stubdps.azure-devices-provisioning.net' -and (@($Info.Dps.LinkedIotHubs) -join ',') -eq 'stubhub.service.azure-devices.net' -and $Info.Dps.ConnectionString -like 'HostName=stubdps.*') "full: DPS info: $($Info.Dps.ToHashtable() | ConvertTo-Json -Compress -Depth 3)"
Assert ($Info.AdrPolicy.NamespaceName -eq 'azure-adr-ns' -and $Info.AzureResourceGroup -eq 'StubRg') "full: ADR policy or resource group not returned."
$RoundTrip = & $Module { param($Json) [TestEnvironmentInfo]::FromJson($Json) } $Info.ToJson()
Assert ($RoundTrip.IotHub.ConnectionProfile -eq 'MqttV5' -and $RoundTrip.IotHub.ServiceFqdn -eq $Info.IotHub.ServiceFqdn -and $RoundTrip.IotHub.DeviceFqdn -eq $Info.IotHub.DeviceFqdn) "full: the MQTT v5 hub fields do not survive a JSON round trip."

# Defaults: local auth on, no telemetry Event Hub, and a link that keeps the topic groups needs no extra write.
Reset-Stub
$Info = New-AzIotMqttv5TestEnvironment @EnvArgs
$HubPuts = Find-Calls $HubPutPattern
Assert ($HubPuts.Count -eq 1) "defaults: expected only the hub create PUT, got $($HubPuts.Count)."
Assert (($Stub.Calls[$HubPuts[0]].Body | ConvertFrom-Json).properties.disableLocalAuth -eq $false) "defaults: local auth must stay enabled."
Assert (@($Stub.RoleAssignments | ?{ $_ -like 'caller-oid|*' }).Count -eq 0) "defaults: the caller must not be granted a data-plane role."
Assert (@(Find-Calls '^eventhubs ').Count -eq 0 -and $null -eq $Info.IotHub.TelemetryEventHub) "defaults: no telemetry Event Hub expected."
Assert (@(Find-Calls '^iot hub ').Count -eq 0) "defaults: 'az iot hub' must not be called."
Assert (-not $Info.IotHub.LocalAuthDisabled -and (@($Info.IotHub.EventHub.ConsumerGroups) -join ',') -eq '$Default') "defaults: hub info: $($Info.IotHub.ToHashtable() | ConvertTo-Json -Compress -Depth 3)"

# Invalid arguments fail before anything is called.
foreach ($Case in @(
    @{ Name = 'template-variable'; Args = @{ TopicTemplates = @('e2e/{moduleId}/#') }; Error = 'not allowed' },
    @{ Name = 'template-reserved'; Args = @{ TopicTemplates = @('ih/x') }; Error = 'not allowed' },
    @{ Name = 'template-wildcard'; Args = @{ TopicTemplates = @('#') }; Error = 'not allowed' },
    @{ Name = 'telemetry-groups'; Args = @{ TelemetryEventHubConsumerGroups = @('t-0') }; Error = 'requires -RouteTelemetryToEventHub' }
)) {
    Reset-Stub
    $Thrown = $null
    try { $CaseArgs = $Case.Args; New-AzIotMqttv5TestEnvironment @EnvArgs @CaseArgs | Out-Null } catch { $Thrown = $_.Exception.Message }
    Assert ("$Thrown" -match $Case.Error -and $Stub.Calls.Count -eq 0) "$($Case.Name): expected '$($Case.Error)' before any call; got '$Thrown' after $($Stub.Calls.Count) call(s)."
}

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: MQTT v5 test environment."
