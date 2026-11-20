<#
.SYNOPSIS
Drives Add-AzIotEventHubTelemetryRoute and New-AzIotTestEnvironment -RouteTelemetryToEventHub with
`az` stubbed, and checks the Event Hub, roles, endpoint and routes they set up, that running again
changes nothing, and the C test configuration rendered from the result.

.DESCRIPTION
Provisions nothing and needs no credentials. `az` is replaced by a stub that records every call
and keeps the Event Hub, consumer groups, role assignments and hub routing it was asked to create.

.EXAMPLE
pwsh -NoProfile -File tests/Test-TelemetryEventHubRoute.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $RepoRoot 'scripts/AzIotSdkTest/AzIotSdkTest.psd1') -Force
$Module = Get-Module AzIotSdkTest
& $Module {
    function script:Start-Sleep { }
    function script:Install-AzureIotCliExtension { }
    function script:Wait-AzRoleAssignment { }
}

function global:Reset-Stub {
    $global:Stub = @{
        Calls = New-Object System.Collections.Generic.List[string]
        EventHubs = @()
        ConsumerGroups = @('$Default')
        RoleAssignments = @()
        RoleAssignmentCreatedOn = @{}
        Endpoints = @()
        Routes = @()
        EndpointFailures = 0
    }
}

function global:New-StubEndpoint([string]$Uri = 'sb://ehns-stub.servicebus.windows.net/', [string]$AuthenticationType = 'identityBased', $Identity = $null) {
    [pscustomobject]@{ name = 'telemetry'; endpointUri = $Uri; entityPath = 'telemetry'; authenticationType = $AuthenticationType; identity = $Identity }
}

function global:New-StubRoute([string]$Name = 'telemetry', [string]$Endpoint = 'telemetry', [bool]$Enabled = $true, [string]$Condition = 'true', [string]$Source = 'DeviceMessages') {
    [pscustomobject]@{ name = $Name; source = $Source; condition = $Condition; endpointNames = @($Endpoint); isEnabled = $Enabled }
}

function global:az {
    $Argv = @($args | %{ "$_" })
    $Joined = $Argv -join ' '
    $global:Stub.Calls.Add($Joined)
    $global:LASTEXITCODE = 0
    function Opt([string]$Name) { $i = [array]::IndexOf($Argv, $Name); if ($i -ge 0) { $Argv[$i + 1] } }

    switch -Regex ($Joined) {
        '^account show' { return '{"id":"00000000-0000-0000-0000-000000000000","user":{"name":"stub","type":"servicePrincipal"}}' }
        '^account get-access-token' { return "e30.$([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"oid":"caller-oid"}')).TrimEnd('=')).sig" }
        '^group show' { return 'eastus2euap' }
        '^group exists' { return 'false' }
        '^rest ' { return '{"id":"/subscriptions/0/resourceGroups/StubRg","properties":{"provisioningState":"Succeeded"}}' }
        '^eventhubs namespace create' { return "{`"name`":`"$(Opt '--name')`",`"serviceBusEndpoint`":`"https://$(Opt '--name').servicebus.windows.net:443/`"}" }
        '^eventhubs eventhub list' { return (ConvertTo-Json -Depth 5 -InputObject @($global:Stub.EventHubs)) }
        '^eventhubs eventhub create' {
            $EventHub = [pscustomobject]@{ name = (Opt '--name'); partitionCount = [int](Opt '--partition-count'); id = "/eh/$(Opt '--namespace-name')/$(Opt '--name')" }
            $global:Stub.EventHubs += $EventHub
            return ($EventHub | ConvertTo-Json)
        }
        '^eventhubs eventhub consumer-group list' { return $global:Stub.ConsumerGroups }
        '^eventhubs eventhub consumer-group create' { $global:Stub.ConsumerGroups += (Opt '--name'); return '' }
        '^iot hub identity assign' { return 'hub-principal' }
        '^role assignment list' {
            $Principal = if ((Opt '--query') -match "principalId=='([^']+)'") { $Matches[1] }
            $Key = "$Principal|$(Opt '--role')|$(Opt '--scope')"
            return (ConvertTo-Json -InputObject @($global:Stub.RoleAssignments | ?{ $_ -eq $Key } | %{ @{ createdOn = $global:Stub.RoleAssignmentCreatedOn[$_] } }))
        }
        '^role assignment create' {
            $Key = "$(Opt '--assignee-object-id')|$(Opt '--role')|$(Opt '--scope')"
            $global:Stub.RoleAssignments += $Key
            $global:Stub.RoleAssignmentCreatedOn[$Key] = [DateTimeOffset]::UtcNow.ToString('o')
            return ''
        }
        '^iot hub show' { return (@{ endpoints = @{ eventHubs = @($global:Stub.Endpoints) }; routes = @($global:Stub.Routes) } | ConvertTo-Json -Depth 5) }
        '^iot hub message-endpoint create eventhub' {
            if ($global:Stub.EndpointFailures -gt 0) {
                $global:Stub.EndpointFailures--
                $global:LASTEXITCODE = 1
                Write-Error -ErrorAction Continue '(400049) Unauthorized: the managed identity could not authenticate to the Event Hub. errorcode: IH400049.'
                return
            }
            $global:Stub.Endpoints += New-StubEndpoint -Uri (Opt '--endpoint-uri')
            return ''
        }
        '^iot hub message-route create' { $global:Stub.Routes += New-StubRoute -Name (Opt '--route-name') -Endpoint (Opt '--endpoint-name'); return '' }
        '^iot hub create' { return '{"id":"/hub","properties":{"eventHubEndpoints":{"events":{"path":"stubhub","partitionCount":2}}}}' }
        '^iot hub connection-string show' { return 'HostName=stubhub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=RkFLRQ==' }
        '^iot hub consumer-group list' { return '[{"name":"$Default"}]' }
        default { return '' }
    }
}

$Problems = New-Object System.Collections.Generic.List[string]
function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { $Problems.Add($Message) } }
function Find-Call([string]$Pattern) { for ($i = 0; $i -lt $Stub.Calls.Count; $i++) { if ($Stub.Calls[$i] -match $Pattern) { return $i } }; return -1 }
function Count-Calls([string]$Pattern) { @($Stub.Calls | ?{ $_ -match $Pattern }).Count }

$Route = @{ ResourceGroup = 'StubRg'; IotHubName = 'stubhub'; NamespaceName = 'ehns-stub'; ConsumerGroups = @('e2e-0', 'e2e-1') }
$Sender = '2b629674-e913-4c01-ae53-ef4638d8f975'
$Receiver = 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'

# A new route: an Entra-only namespace, both roles, an identity-based endpoint and one route.
Reset-Stub
$Started = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$Info = Add-AzIotEventHubTelemetryRoute @Route -ReaderServicePrincipalIds 'ci-principal'
Assert ((Find-Call '^eventhubs namespace create --name ehns-stub .*--location eastus2euap .*--disable-local-auth true --minimum-tls-version 1.2') -ge 0) "new: the namespace must be created with local auth disabled and TLS 1.2 in the resource group's location."
Assert ((Find-Call '^eventhubs eventhub create --name telemetry .*--partition-count 4') -ge 0) "new: Event Hub 'telemetry' with 4 partitions not created."
Assert ((Count-Calls '^eventhubs eventhub consumer-group create') -eq 2) "new: expected 2 consumer groups created."
$Scope = '/eh/ehns-stub/telemetry'
foreach ($Expected in "hub-principal|$Sender|$Scope", "caller-oid|$Receiver|$Scope", "ci-principal|$Receiver|$Scope") {
    Assert ($Stub.RoleAssignments -contains $Expected) "new: missing role assignment $Expected."
}
Assert ((Find-Call '^role assignment create --assignee-object-id caller-oid --assignee-principal-type ServicePrincipal') -ge 0) "new: the signed-in principal's type must be passed."
Assert ((Find-Call "^iot hub message-endpoint create eventhub .*--endpoint-uri sb://ehns-stub.servicebus.windows.net --entity-path telemetry --identity \[system\]") -ge 0) "new: the endpoint must target the Event Hub with the hub's system identity."
Assert ((Find-Call '^iot hub message-endpoint create') -gt (Find-Call "^role assignment create --assignee-object-id hub-principal")) "new: the hub's Data Sender grant must precede its endpoint."
Assert (($Stub.Routes.name -join ',') -eq 'telemetry') "new: routes are '$($Stub.Routes.name -join ',')', expected 'telemetry' only."
Assert ($Info.GetConnectionString() -eq 'Endpoint=sb://ehns-stub.servicebus.windows.net/;EntityPath=telemetry') "new: connection string is '$($Info.GetConnectionString())'."
Assert (($Info.ConsumerGroups -join ',') -eq '$Default,e2e-0,e2e-1' -and $Info.PartitionCount -eq 4) "new: returned consumer groups '$($Info.ConsumerGroups -join ',')', partitions $($Info.PartitionCount)."
Assert ($Info.ReadableAfterUnixSeconds -ge $Started + 300) "new: readers must wait for their new roles to apply."

# Running again changes nothing, and readers still wait for the roles granted moments ago.
$Stub.Calls.Clear()
$Info = Add-AzIotEventHubTelemetryRoute @Route -ReaderServicePrincipalIds 'ci-principal'
$Writes = @($Stub.Calls | ?{ $_ -match '^(eventhubs eventhub create|eventhubs eventhub consumer-group create|role assignment create|iot hub message-endpoint create|iot hub message-route create)' })
Assert ($Writes.Count -eq 0) "rerun: expected no new resources, got: $($Writes -join ' | ')"
Assert ($Info.ReadableAfterUnixSeconds -ge $Started + 300) "rerun: readers must still wait for the roles the first run granted."

# Readers need not wait for roles granted long ago, but do when a role's age is unknown.
foreach ($Key in @($Stub.RoleAssignmentCreatedOn.Keys)) { $Stub.RoleAssignmentCreatedOn[$Key] = [DateTimeOffset]::UtcNow.AddHours(-1).ToString('o') }
$Info = Add-AzIotEventHubTelemetryRoute @Route -ReaderServicePrincipalIds 'ci-principal'
Assert ($Info.ReadableAfterUnixSeconds -le [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) "old-roles: readers should not wait for roles granted an hour ago."
$Stub.RoleAssignmentCreatedOn["ci-principal|$Receiver|/eh/ehns-stub/telemetry"] = $null
$Started = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$Info = Add-AzIotEventHubTelemetryRoute @Route -ReaderServicePrincipalIds 'ci-principal'
Assert ($Info.ReadableAfterUnixSeconds -ge $Started + 300) "unknown-age: readers must wait when a role's creation time is unknown."

# The built-in route is created first when asked for; one already there is kept.
Reset-Stub
$Stub.Routes = @(New-StubRoute)
$Stub.Endpoints = @(New-StubEndpoint)
Add-AzIotEventHubTelemetryRoute @Route -KeepBuiltInEndpointRoute | Out-Null
Assert ((Find-Call '^iot hub message-route create .*--route-name builtin-events --endpoint-name events') -ge 0) "builtin: route to the built-in endpoint not created."
Assert ((Count-Calls '^iot hub message-route create') -eq 1) "builtin: the existing telemetry route must be kept."
Reset-Stub
Add-AzIotEventHubTelemetryRoute @Route -KeepBuiltInEndpointRoute | Out-Null
Assert (($Stub.Routes.name -join ',') -eq 'builtin-events,telemetry') "builtin: routes are '$($Stub.Routes.name -join ',')', expected the built-in route first."

# An Event Hub named like the built-in route is refused before anything is provisioned.
Reset-Stub
$Failed = $false
try { Add-AzIotEventHubTelemetryRoute @Route -EventHubName 'builtin-events' -KeepBuiltInEndpointRoute | Out-Null } catch { $Failed = $_.Exception.Message -match 'built-in endpoint' }
Assert ($Failed -and $Stub.Calls.Count -eq 0) "builtin-name: should fail before any az call when -EventHubName is 'builtin-events'."

# An endpoint refused until the hub's role applies is retried.
Reset-Stub
$Stub.EndpointFailures = 2
Add-AzIotEventHubTelemetryRoute @Route | Out-Null
Assert ((Count-Calls '^iot hub message-endpoint create') -eq 3) "endpoint-retry: expected 3 attempts, got $(Count-Calls '^iot hub message-endpoint create')."

# An endpoint of the same name for another Event Hub, or sending with another identity, is not reused.
$Mismatches = [ordered]@{
    'another Event Hub' = New-StubEndpoint -Uri 'sb://other.servicebus.windows.net'
    'a key' = New-StubEndpoint -AuthenticationType 'keyBased'
    'a user-assigned identity' = New-StubEndpoint -Identity ([pscustomobject]@{ userAssignedIdentity = '/uami' })
}
foreach ($Mismatch in $Mismatches.Keys) {
    Reset-Stub
    $Stub.Endpoints = @($Mismatches[$Mismatch])
    $Failed = $false
    try { Add-AzIotEventHubTelemetryRoute @Route | Out-Null } catch { $Failed = $_.Exception.Message -match 'already has an endpoint' }
    Assert $Failed "endpoint-mismatch: should fail on an endpoint that uses $Mismatch."
}

# A route of the same name that does not send all device messages to its endpoint is not reused.
$Mismatches = [ordered]@{
    'disabled' = New-StubRoute -Enabled $false
    'filtered' = New-StubRoute -Condition '$body.level = "critical"'
    'to another endpoint' = New-StubRoute -Endpoint 'other'
    'for twin changes' = New-StubRoute -Source 'TwinChangeEvents'
    'built-in, disabled' = New-StubRoute -Name 'builtin-events' -Endpoint 'events' -Enabled $false
}
foreach ($Mismatch in $Mismatches.Keys) {
    Reset-Stub
    $Stub.Endpoints = @(New-StubEndpoint)
    $Stub.Routes = @($Mismatches[$Mismatch])
    $Failed = $false
    try { Add-AzIotEventHubTelemetryRoute @Route -KeepBuiltInEndpointRoute | Out-Null } catch { $Failed = $_.Exception.Message -match 'already has a route' }
    Assert $Failed "route-mismatch: should fail on an existing route that is $Mismatch."
}

# New-AzIotTestEnvironment keeps the built-in route only while the built-in endpoint is readable.
foreach ($DisableLocalAuth in $false, $true) {
    Reset-Stub
    $TestEnvInfo = New-AzIotTestEnvironment -ResourceGroup StubRg -AzureLocation eastus2euap -IotHubName stubhub -NoDps `
        -RouteTelemetryToEventHub -TelemetryEventHubConsumerGroups e2e-0 -DisableLocalAuth:$DisableLocalAuth
    $Name = "environment (DisableLocalAuth=$DisableLocalAuth)"
    $Expected = if ($DisableLocalAuth) { 'telemetry' } else { 'builtin-events,telemetry' }
    Assert (($Stub.Routes.name -join ',') -eq $Expected) "$($Name): routes are '$($Stub.Routes.name -join ',')', expected '$Expected'."
    Assert ($TestEnvInfo.IotHub.TelemetryEventHub.Name -eq 'telemetry') "$($Name): TelemetryEventHub not set."
    Assert ((Count-Calls '^eventhubs eventhub consumer-group create --name e2e-0') -eq 1) "$($Name): consumer group e2e-0 not created."
}

# The test environment round-trips through JSON, and the C config reads the routed Event Hub. Run
# in the module's scope, where its classes are visible.
$OutDir = Join-Path ([IO.Path]::GetTempPath()) "telemetry-test-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $OutDir | Out-Null
try {
    $Rendered = & $Module {
        param($TestEnvInfo, $OutDir)
        $RoundTripped = [TestEnvironmentInfo]::FromJson($TestEnvInfo.ToJson())
        $Empty = [TestEnvironmentInfo]::FromJson([TestEnvironmentInfo]::new().ToJson())

        function New-StubCertificate {
            $Key = [Security.Cryptography.RSA]::Create(2048)
            $Request = [Security.Cryptography.X509Certificates.CertificateRequest]::new('CN=stub', $Key,
                [Security.Cryptography.HashAlgorithmName]::SHA256, [Security.Cryptography.RSASignaturePadding]::Pkcs1)
            $Certificate = $Request.CreateSelfSigned([DateTimeOffset]::UtcNow, [DateTimeOffset]::UtcNow.AddDays(1))
            return [X509CertificateInfo]::new($Key, $Certificate)
        }
        $RoundTripped.IotHub.Devices.X509Thumbprint += [IotHubX509IdentityInfo]::new('stub-device', $null, (New-StubCertificate), $null)
        $RoundTripped.Dps.Enrollments.IndividualX509 += [DpsX509IndividualEnrollmentInfo]::new('stub-enrollment', (New-StubCertificate))
        $RoundTripped.Dps.RootCaCertificates += New-StubCertificate

        $Configs = @{}
        foreach ($Target in 'powershell', 'bash') {
            $File = Join-Path $OutDir "config-$Target"
            New-AzIotCSDKE2ETestConfig -TestEnvInfo $RoundTripped -Target $Target -OutFile $File | Out-Null
            $Configs[$Target] = Get-Content -Raw $File
        }
        [pscustomobject]@{ TelemetryEventHub = $RoundTripped.IotHub.TelemetryEventHub; EmptyTelemetryEventHub = $Empty.IotHub.TelemetryEventHub; Configs = $Configs }
    } $TestEnvInfo $OutDir

    $Routed = $Rendered.TelemetryEventHub
    Assert ($Routed.FullyQualifiedNamespace -like '*.servicebus.windows.net' -and $Routed.ReadableAfterUnixSeconds -gt 0) "json: TelemetryEventHub lost in the round trip."
    Assert ($null -eq $Rendered.EmptyTelemetryEventHub) "json: a missing TelemetryEventHub must stay null."
    foreach ($Target in 'powershell', 'bash') {
        $Config = $Rendered.Configs[$Target]
        foreach ($Expected in @(
            "IOTHUB_EVENTHUB_CONNECTION_STRING\W+Endpoint=sb://$([regex]::Escape($Routed.FullyQualifiedNamespace))/;EntityPath=telemetry`""
            'IOTHUB_EVENTHUB_LISTEN_NAME\W+telemetry"'
            'IOTHUB_PARTITION_COUNT\W+4\b'
            'IOTHUB_EVENTHUB_PARTITION_COUNT\W+4"'
            "IOTHUB_EVENTHUB_READABLE_AFTER_UNIX_SECONDS\W+$($Routed.ReadableAfterUnixSeconds)`""
        )) {
            Assert ($Config -match $Expected) "config ($Target): no line matching $Expected."
        }
    }
}
finally {
    Remove-Item -Recurse -Force -Path $OutDir -ErrorAction SilentlyContinue
}

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: device telemetry routed to an Entra-only Event Hub."
