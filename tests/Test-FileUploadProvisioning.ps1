<#
.SYNOPSIS
Drives the provision-e2e-resources action script and New-AzIotTestEnvironment with `az` stubbed, and
checks how file upload is configured with and without certificate management.

.DESCRIPTION
Provisions nothing and needs no credentials. `az` is replaced by a stateful stub that records every
call and keeps the hub resource, so the final hub state can be asserted. The stub reproduces the
azure-iot extension's `az iot hub update`, which refuses a non-GEN2 hub whose GET carries
properties.deviceRegistry -- what an ADR link leaves on the hub.

Each scenario runs in a child process, because Stop-OnError exits the host.

.PARAMETER TranscriptDir
When set, each scenario's recorded `az` calls are kept there (<scenario>.jsonl).

.EXAMPLE
pwsh -NoProfile -File tests/Test-FileUploadProvisioning.ps1
#>
[CmdletBinding()]
param(
    [string]$TranscriptDir = $null,
    # Internal: runs one scenario in this process.
    [string]$RunScenario = $null,
    [string]$StateDir = $null
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ModulePath = Join-Path $RepoRoot 'scripts/AzIotSdkTest/AzIotSdkTest.psd1'
$ActionPath = Join-Path $RepoRoot 'actions/provision-e2e-resources/action.yml'
$global:FakeStorageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=stoaccfake;AccountKey=RkFLRQ==;EndpointSuffix=core.windows.net'

function Get-ActionInlineScript {
    param([string]$Path)

    $Lines = Get-Content -Path $Path
    $Start = -1
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^(\s*)inlineScript:\s*\|\s*$') { $Start = $i; $Indent = $Matches[1].Length; break }
    }
    if ($Start -lt 0) { throw "No inlineScript in $Path." }

    $Body = New-Object System.Collections.Generic.List[string]
    for ($i = $Start + 1; $i -lt $Lines.Count; $i++) {
        $Line = $Lines[$i]
        if ($Line.Trim().Length -gt 0 -and ($Line.Length - $Line.TrimStart().Length) -le $Indent) { break }
        $Body.Add($Line)
    }
    $Strip = ($Body | ?{ $_.Trim().Length -gt 0 } | %{ $_.Length - $_.TrimStart().Length } | Measure-Object -Minimum).Minimum
    return (($Body | %{ if ($_.Length -ge $Strip) { $_.Substring($Strip) } else { '' } }) -join "`n")
}

if ($RunScenario) {
    # ---- child process: one scenario ---------------------------------------------------------
    $global:StubState = @{
        Log = Join-Path $StateDir "$RunScenario.jsonl"
        Resources = @{}
        Linked = $false
    }

    function global:Get-StubKey([string]$Url) { ([uri]$Url).AbsolutePath.ToLowerInvariant() }

    function global:Get-StubHubKey {
        @($global:StubState.Resources.Keys | ?{ $_ -like '*/microsoft.devices/iothubs/*' })[0]
    }

    function global:az {
        $Argv = @($args | %{ "$_" })
        $Joined = $Argv -join ' '
        $Body = $null
        $BodyIndex = [array]::IndexOf($Argv, '--body')
        if ($BodyIndex -ge 0 -and $Argv[$BodyIndex + 1].StartsWith('@')) {
            $Body = Get-Content -Raw -Path $Argv[$BodyIndex + 1].Substring(1)
        }
        Add-Content -Path $global:StubState.Log -Value (@{ argv = $Argv; body = $Body } | ConvertTo-Json -Compress -Depth 5)
        $global:LASTEXITCODE = 0

        function Opt([string]$Name) { $i = [array]::IndexOf($Argv, $Name); if ($i -ge 0) { $Argv[$i + 1] } }

        switch -Regex ($Joined) {
            '^account show' { return '{"id":"00000000-0000-0000-0000-000000000000","user":{"name":"stub"}}' }
            '^extension list' { if ($Joined -match 'table') { return 'azure-iot 0.30.0b2' } return '[{"name":"azure-iot","version":"0.30.0b2"}]' }
            '^group exists' { return 'false' }
            '^rest ' {
                $Url = Opt '--url'
                $Method = Opt '--method'
                if ($Url -notmatch 'management\.azure\.com') {
                    # DPS enrollment data plane.
                    return '{"attestation":{"symmetricKey":{"primaryKey":"a","secondaryKey":"b"}}}'
                }
                $Key = Get-StubKey $Url
                if ($Method -eq 'PUT') {
                    $Resource = $Body | ConvertFrom-Json
                    $Resource | Add-Member -Force id ([uri]$Url).AbsolutePath
                    if ($null -eq $Resource.properties) { $Resource | Add-Member -Force properties ([pscustomobject]@{}) }
                    $Resource.properties | Add-Member -Force provisioningState 'Succeeded'
                    $Resource.properties | Add-Member -Force idScope '0ne00000000'
                    $Resource.properties | Add-Member -Force eventHubEndpoints ([pscustomobject]@{ events = [pscustomobject]@{ path = 'hub'; partitionCount = 4 } })
                    if ($Resource.identity) { $Resource.identity | Add-Member -Force principalId ([guid]::NewGuid().ToString()) }
                    $global:StubState.Resources[$Key] = $Resource
                    return ($Resource | ConvertTo-Json -Depth 20)
                }
                if ($global:StubState.Resources.ContainsKey($Key)) {
                    return ($global:StubState.Resources[$Key] | ConvertTo-Json -Depth 20)
                }
                return '{"properties":{"provisioningState":"Succeeded"}}'
            }
            '^iot hub create' {
                $Name = Opt '--name'
                $Key = "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/$((Opt '--resource-group').ToLowerInvariant())/providers/microsoft.devices/iothubs/$($Name.ToLowerInvariant())"
                $global:StubState.Resources[$Key] = [pscustomobject]@{
                    id = $Key; sku = [pscustomobject]@{ name = 'S1' }
                    properties = [pscustomobject]@{ eventHubEndpoints = [pscustomobject]@{ events = [pscustomobject]@{ path = 'hub'; partitionCount = 4 } } }
                }
                return ($global:StubState.Resources[$Key] | ConvertTo-Json -Depth 20)
            }
            '^iot hub update' {
                # The azure-iot extension's update: GET, then refuse any non-GEN2 hub carrying ADR properties.
                $Hub = $global:StubState.Resources[(Get-StubHubKey)]
                if ($Hub.properties.deviceRegistry.namespaceResourceId -and $Hub.sku.name -ne 'GEN2') {
                    Write-Host 'ERROR: ADR properties are only supported for Generation2 IoT Hub SKUs.'
                    $global:LASTEXITCODE = 1
                    return
                }
                if (Opt '--fc') {
                    $Hub.properties | Add-Member -Force storageEndpoints ([pscustomobject]@{ '$default' = [pscustomobject]@{
                        connectionString = (Opt '--fcs'); containerName = (Opt '--fc'); sasTtlAsIso8601 = "PT$(Opt '--fileupload-sas-ttl')H" } })
                }
                if ((Opt '--fileupload-notifications') -eq 'true') {
                    $Hub.properties | Add-Member -Force enableFileUploadNotifications $true
                }
                return ''
            }
            '^iot hub connection-string show' { return 'HostName=stubhub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=RkFLRQ==' }
            '^iot hub consumer-group list' { return '[{"name":"$Default"}]' }
            '^iot hub device-identity create' { return '{"authentication":{"symmetricKey":{"primaryKey":"a","secondaryKey":"b"}}}' }
            '^iot hub device-identity connection-string show' { return '{"connectionString":"HostName=hub.azure-devices.net;DeviceId=d;x509=true"}' }
            '^iot dps create' { return '{"id":"/dps","properties":{"idScope":"0ne00000000","deviceProvisioningHostName":"global.azure-devices-provisioning.net","serviceOperationsHostName":"dps.azure-devices-provisioning.net"}}' }
            '^iot dps connection-string show' { return 'HostName=dps.azure-devices-provisioning.net;SharedAccessKeyName=provisioningserviceowner;SharedAccessKey=RkFLRQ==' }
            '^iot dps certificate show' { return 'etag' }
            '^iot dps certificate generate-verification-code' { return '{"properties":{"verificationCode":"code"}}' }
            '^storage account show-connection-string' { return $global:FakeStorageConnectionString }
            default { return '' }
        }
    }

    Import-Module $ModulePath -Force
    $Module = Get-Module AzIotSdkTest
    # ADR and RBAC plumbing is out of scope here; what matters is that the hub is linked, which is
    # what puts properties.deviceRegistry on it.
    & $Module {
        function script:Start-Sleep { }
        function script:Install-AzureIotCliExtension { }
        function script:Wait-AzRoleAssignment { }
        function script:New-AdrNamespace { [pscustomobject]@{ id = '/adr'; identity = [pscustomobject]@{ principalId = 'adr-principal' } } }
        function script:New-AdrCertificateAuthority { }
        function script:Sync-DpsAdrConfiguration { }
        function script:Connect-AdrNamespace {
            param($NamespaceId, $Location, $IotHubId, $DpsId, $ExpectedPrincipalId)
            Add-Content -Path $global:StubState.Log -Value '{"argv":["<Connect-AdrNamespace>"]}'
            $Hub = $global:StubState.Resources[(Get-StubHubKey)]
            $Hub.properties | Add-Member -Force deviceRegistry ([pscustomobject]@{ namespaceResourceId = $NamespaceId })
            if ($global:StubState.LinkDropsFileUpload) {
                $Hub.properties.PSObject.Properties.Remove('storageEndpoints')
            }
        }
    }

    $env:AZ_IOT_MODULE = $ModulePath
    $env:AZ_IOT_RG_NAME = 'StubRg'
    $env:AZ_IOT_RG_PREFIX = ''
    $env:AZ_IOT_LOCATION = 'eastus2euap'
    $env:AZ_IOT_ENABLE_ADU = 'None'
    $env:AZ_IOT_ENABLE_CERT_MGMT = if ($RunScenario -like 'cert-mgmt*') { 'true' } else { 'false' }
    $global:StubState.LinkDropsFileUpload = ($RunScenario -eq 'cert-mgmt-link-drops-file-upload')
    $env:AZ_IOT_ENABLE_FILE_UPLOAD = 'true'
    $env:AZ_IOT_HUB_X509_DEVICES = '1'
    $env:AZ_IOT_DPS_INDIVIDUAL = '1'
    $env:AZ_IOT_DPS_GROUP_DEVICES = '0'
    $env:AZ_IOT_CONFIG_CMDLET = 'New-AzIotCSDKE2ETestConfig'
    $env:AZ_IOT_CONFIG_TARGET = 'bash'
    $env:AZ_IOT_OUT_FILE = Join-Path $StateDir "$RunScenario-config.sh"
    $env:GITHUB_OUTPUT = Join-Path $StateDir "$RunScenario-output.txt"

    # Fixed resource names keep transcripts comparable across module versions.
    $Script = Get-ActionInlineScript -Path $ActionPath
    $Call = 'New-AzIotTestEnvironment @NewEnvArgs'
    if ([regex]::Matches($Script, [regex]::Escape($Call)).Count -ne 1) { throw "Expected exactly one '$Call' in the action script." }
    $Script = $Script.Replace($Call, "$Call -IotHubName stubhub -DpsName stubdps -StorageAccountName stoaccstub")

    . ([scriptblock]::Create($Script))

    $Hub = $global:StubState.Resources[(Get-StubHubKey)]
    Set-Content -Path (Join-Path $StateDir "$RunScenario-hub.json") -Value ($Hub | ConvertTo-Json -Depth 20)
    exit 0
}

# ---- parent: run scenarios and assert ----------------------------------------------------------
$Pwsh = (Get-Process -Id $PID).Path
$StateDir = Join-Path ([IO.Path]::GetTempPath()) "fu-test-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $StateDir | Out-Null
$Problems = New-Object System.Collections.Generic.List[string]

function Invoke-Scenario([string]$Name) {
    $Output = & $Pwsh -NoProfile -File $PSCommandPath -RunScenario $Name -StateDir $StateDir 2>&1 | Out-String
    $ExitCode = $LASTEXITCODE
    $LogPath = Join-Path $StateDir "$Name.jsonl"
    $Calls = @()
    if (Test-Path $LogPath) { $Calls = @(Get-Content $LogPath | %{ $_ | ConvertFrom-Json }) }
    $HubPath = Join-Path $StateDir "$Name-hub.json"
    $Hub = if (Test-Path $HubPath) { Get-Content -Raw $HubPath | ConvertFrom-Json } else { $null }
    if ($TranscriptDir) {
        New-Item -ItemType Directory -Force -Path $TranscriptDir | Out-Null
        Copy-Item $LogPath (Join-Path $TranscriptDir "$Name.jsonl") -ErrorAction SilentlyContinue
    }
    [pscustomobject]@{ Name = $Name; ExitCode = $ExitCode; Output = $Output; Calls = $Calls; Hub = $Hub }
}

function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { $Problems.Add($Message) } }

function Find-Call($Run, [scriptblock]$Predicate) {
    for ($i = 0; $i -lt $Run.Calls.Count; $i++) { if (& $Predicate ($Run.Calls[$i].argv -join ' ') $Run.Calls[$i]) { return $i } }
    return -1
}

function Assert-FileUploadState($Run) {
    $Default = $Run.Hub.properties.storageEndpoints.'$default'
    Assert ($Default.containerName -eq 'iothubuploads') "$($Run.Name): hub storageEndpoints.`$default.containerName is '$($Default.containerName)'."
    Assert ($Default.connectionString -eq $FakeStorageConnectionString) "$($Run.Name): hub storage connection string not set."
    Assert ($Default.sasTtlAsIso8601 -eq 'PT1H') "$($Run.Name): hub sasTtlAsIso8601 is '$($Default.sasTtlAsIso8601)'."
    Assert ($Run.Hub.properties.enableFileUploadNotifications -eq $true) "$($Run.Name): hub enableFileUploadNotifications is not true."
}

try {
    # Certificate management + file upload: no `az iot hub update` may run once the hub is linked.
    $Run = Invoke-Scenario 'cert-mgmt'
    Assert ($Run.ExitCode -eq 0) "cert-mgmt: provisioning exited $($Run.ExitCode): $(($Run.Output -split "`n" | Select-String 'ERROR' | Select-Object -First 3) -join ' | ')"
    $HubPut = Find-Call $Run { param($j, $c) $j -match '^rest --method PUT .*/IotHubs/stubhub\?' }
    $Link = Find-Call $Run { param($j) $j -eq '<Connect-AdrNamespace>' }
    $Storage = Find-Call $Run { param($j) $j -match '^storage account create' }
    $Container = Find-Call $Run { param($j) $j -match '^storage container create' }
    Assert ($HubPut -ge 0 -and $Link -gt $HubPut) "cert-mgmt: hub PUT ($HubPut) must precede the ADR link ($Link)."
    Assert ($Storage -ge 0 -and $Storage -lt $HubPut -and $Container -lt $HubPut) "cert-mgmt: storage account ($Storage) and container ($Container) must be created before the hub PUT ($HubPut)."
    Assert ((Find-Call $Run { param($j) $j -match '^iot hub update' }) -lt 0) "cert-mgmt: 'az iot hub update' must not be called."
    if ($HubPut -ge 0) {
        $Body = $Run.Calls[$HubPut].body | ConvertFrom-Json
        $Default = $Body.properties.storageEndpoints.'$default'
        Assert ($Default.containerName -eq 'iothubuploads' -and $Default.connectionString -eq $FakeStorageConnectionString -and $Default.sasTtlAsIso8601 -eq 'PT1H') "cert-mgmt: hub PUT body lacks storageEndpoints.`$default: $($Run.Calls[$HubPut].body)"
        Assert ($Body.properties.enableFileUploadNotifications -eq $true) "cert-mgmt: hub PUT body lacks enableFileUploadNotifications=true."
        Assert ($Body.sku.name -eq 'S1' -and $Body.identity.type -eq 'SystemAssigned' -and $Body.properties.disableLocalAuth -eq $false -and $Body.properties.minTlsVersion -eq '1.2') "cert-mgmt: hub PUT body lost its existing settings."
        Assert (($Run.Calls[$HubPut].argv -join ' ') -match 'api-version=2026-06-01-preview') "cert-mgmt: hub PUT not at the module's IoT Hub api-version."
    }
    $LastReadBack = -1
    for ($i = 0; $i -lt $Run.Calls.Count; $i++) { if (($Run.Calls[$i].argv -join ' ') -match '^rest --method GET .*/IotHubs/stubhub\?') { $LastReadBack = $i } }
    Assert ($LastReadBack -gt $Link) "cert-mgmt: the hub's file upload settings must be read back after the ADR link."
    Assert-FileUploadState $Run

    # A link that drops the settings must fail provisioning rather than pass it silently.
    $Run = Invoke-Scenario 'cert-mgmt-link-drops-file-upload'
    Assert ($Run.ExitCode -ne 0 -and $Run.Output -match 'lost its file upload settings') "cert-mgmt-link-drops-file-upload: provisioning should fail on the read-back (exit $($Run.ExitCode))."

    # No certificate management: the CLI calls stay exactly as they were.
    $Run = Invoke-Scenario 'no-cert-mgmt'
    Assert ($Run.ExitCode -eq 0) "no-cert-mgmt: provisioning exited $($Run.ExitCode)."
    $Updates = @($Run.Calls | ?{ ($_.argv -join ' ') -match '^iot hub update' } | %{ $_.argv -join ' ' })
    $Expected = @(
        "iot hub update --name stubhub --resource-group StubRg --fcs $FakeStorageConnectionString --fc iothubuploads --fileupload-sas-ttl 1",
        'iot hub update --name stubhub --resource-group StubRg --fileupload-notifications true --only-show-errors'
    )
    Assert (($Updates -join "`n") -ceq ($Expected -join "`n")) "no-cert-mgmt: 'az iot hub update' calls differ:`n  got:      $($Updates -join "`n            ")`n  expected: $($Expected -join "`n            ")"
    Assert ((Find-Call $Run { param($j) $j -match '^rest .*/IotHubs/' }) -lt 0) "no-cert-mgmt: the hub must not be written through ARM."
    Assert ((Find-Call $Run { param($j) $j -match '^iot hub create' }) -lt (Find-Call $Run { param($j) $j -match '^storage account create' })) "no-cert-mgmt: storage must still be created after the hub."
    Assert-FileUploadState $Run
}
finally {
    Remove-Item -Recurse -Force -Path $StateDir -ErrorAction SilentlyContinue
}

if ($Problems.Count -gt 0) {
    $Problems | %{ Write-Host "FAIL: $_" }
    exit 1
}
Write-Host "OK: file upload with and without certificate management."
