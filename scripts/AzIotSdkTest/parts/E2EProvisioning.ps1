
function New-AzIotE2ETestEnvironmentAndConfig {
    <#
    .SYNOPSIS
    Provisions an mqttv3 test environment and writes the test configuration a pipeline runs with.

    .DESCRIPTION
    The single implementation behind actions/provision-e2e-resources and
    vsts/templates/steps-provision-e2e-resources.yaml. Every argument is checked before anything
    touches Azure. Then New-AzIotTestEnvironment provisions the resource group, the config cmdlet
    renders the test configuration to OutFile, and each device of the first X.509 enrollment group
    is appended to it as IOT_DPS_GROUP_X509_CERTIFICATE_<i> (leaf, issuer CA and root, Base64
    PEM), IOT_DPS_GROUP_X509_KEY_<i> and IOT_DPS_GROUP_X509_REGISTRATION_ID_<i>; device 0 also
    without the _<i> suffix. The config cmdlets do not emit those, and PROVISIONING_ROOT_CERT is
    the DPS root, not the group's issuer.

    .PARAMETER ResourceGroup
    Resource group to provision into; created when missing.

    .PARAMETER EnableADU
    None, Gen1 or Gen2. Anything but None needs a module build whose New-AzIotTestEnvironment has
    -EnableADU.

    .PARAMETER RouteTelemetryToEventHub
    Routes device telemetry to an Event Hub with local authentication disabled
    (Add-AzIotEventHubTelemetryRoute).

    .PARAMETER TelemetryEventHubConsumerGroups
    Consumer groups to create on that Event Hub besides $Default, e.g. one per parallel test job.

    .PARAMETER ConfigCmdlet
    Test config renderer exported by this module, e.g. New-AzIotCSDKE2ETestConfig. It must take
    -TestEnvInfo, -Target and -OutFile.

    .OUTPUTS
    The [TestEnvironmentInfo] of the provisioned environment.

    .EXAMPLE
    PS> New-AzIotE2ETestEnvironmentAndConfig -ResourceGroup CSDKE2E-1234-1 -EnableFileUpload -DisableLocalAuth -OutFile test_config/set_test_env_vars.ps1
    #>
    param(
        [Parameter(Mandatory = $true)]
        # Azure allows alphanumerics, underscore, parentheses, hyphen and period, up to 90
        # characters, not ending in a period. \z, not $, so a trailing newline cannot slip through.
        [ValidatePattern('^[A-Za-z0-9._()-]{0,89}[A-Za-z0-9_()-]\z')]
        [string]$ResourceGroup,
        [string]$AzureLocation = "EastUS",
        [ValidateSet('None', 'Gen1', 'Gen2')]
        [string]$EnableADU = 'None',
        [switch]$EnableCertificateManagement,
        [switch]$EnableFileUpload,
        [switch]$DisableLocalAuth,
        [switch]$RouteTelemetryToEventHub,
        [string[]]$TelemetryEventHubConsumerGroups = @(),
        [ValidateRange(0, [int]::MaxValue)]
        [int]$IotHubX509ThumbprintDevices = 1,
        [ValidateRange(0, [int]::MaxValue)]
        [int]$DpsX509IndividualEnrollments = 1,
        [ValidateRange(0, [int]::MaxValue)]
        [int]$DpsX509GroupEnrollmentDevices = 0,
        [ValidateRange(0, [int]::MaxValue)]
        [int]$DpsSymmKeyGroupEnrollmentDevices = 0,
        [string]$ConfigCmdlet = 'New-AzIotCSDKE2ETestConfig',
        [ValidateSet('powershell', 'bash')]
        [string]$ConfigTarget = 'powershell',
        [Parameter(Mandatory = $true)]
        [ValidateScript({ -not [string]::IsNullOrWhiteSpace($_) })]
        [string]$OutFile
    )

    # An exact name among this module's exports, so the caller can never name an arbitrary command.
    $Renderer = $MyInvocation.MyCommand.Module.ExportedFunctions[$ConfigCmdlet]
    if ($null -eq $Renderer) {
        throw "Config cmdlet '$ConfigCmdlet' is not exported by $($MyInvocation.MyCommand.ModuleName)."
    }
    # Matched by unique prefix, as the parameter binder does, so -TargetEnvironment satisfies -Target.
    $MissingParameters = @('TestEnvInfo', 'Target', 'OutFile' | Where-Object {
        $Candidates = @($Renderer.Parameters.Keys -like "$_*")
        -not (($Candidates -contains $_) -or ($Candidates.Count -eq 1))
    })
    if ($MissingParameters.Count -gt 0) {
        throw "Config cmdlet '$ConfigCmdlet' is not a test config renderer: it has no -$($MissingParameters -join ', -') parameter."
    }

    $EnvironmentArguments = @{
        ResourceGroup = $ResourceGroup
        AzureLocation = $AzureLocation
        IotHubX509ThumbprintDevices = $IotHubX509ThumbprintDevices
        DpsX509IndividualEnrollments = $DpsX509IndividualEnrollments
        DpsX509GroupEnrollmentDevices = $DpsX509GroupEnrollmentDevices
        DpsSymmKeyGroupEnrollmentDevices = $DpsSymmKeyGroupEnrollmentDevices
        EnableCertificateManagement = $EnableCertificateManagement
        EnableFileUpload = $EnableFileUpload
        DisableLocalAuth = $DisableLocalAuth
        RouteTelemetryToEventHub = $RouteTelemetryToEventHub
        TelemetryEventHubConsumerGroups = $TelemetryEventHubConsumerGroups
    }
    # Passed only when asked for: master has no -EnableADU, and passing it anyway would fail callers
    # that never wanted ADU with a parameter-binding error.
    if ($EnableADU -ne 'None') {
        if (-not (Get-Command New-AzIotTestEnvironment).Parameters.ContainsKey('EnableADU')) {
            throw "EnableADU is '$EnableADU' but this build of AzIotSdkTest has no New-AzIotTestEnvironment -EnableADU."
        }
        $EnvironmentArguments['EnableADU'] = $EnableADU
    }

    $OutDirectory = Split-Path -Parent $OutFile
    if (-not [string]::IsNullOrWhiteSpace($OutDirectory)) {
        New-Item -ItemType Directory -Force -Path $OutDirectory | Out-Null
    }

    $TestEnvInfo = New-AzIotTestEnvironment @EnvironmentArguments

    & $Renderer -TestEnvInfo $TestEnvInfo -Target $ConfigTarget -OutFile $OutFile | Out-Null

    if ($TestEnvInfo.Dps.Enrollments.GroupX509.Count -gt 0) {
        $Group = $TestEnvInfo.Dps.Enrollments.GroupX509[0]
        $Identities = @($Group.Identities)
        if ($Identities.Count -eq 0) {
            $Identities = @($Group.AddIdentity("csr-bootstrap-$(Get-Random -Minimum 100000 -Maximum 999999)", [timespan]::FromDays(2)))
        }
        for ($i = 0; $i -lt $Identities.Count; $i++) {
            $Identity = $Identities[$i]
            $ChainPem = $Identity.Certificate.ToPem() + "`n" + $Group.Certificate.ToPem() + "`n" + $TestEnvInfo.Dps.RootCaCertificates[0].ToPem()
            $Values = [ordered]@{
                IOT_DPS_GROUP_X509_CERTIFICATE = ConvertTo-Base64 -Content $ChainPem
                IOT_DPS_GROUP_X509_KEY = ConvertTo-Base64 -Content $Identity.Certificate.PrivateKey.ToRsaPkcs1Pem()
                IOT_DPS_GROUP_X509_REGISTRATION_ID = $Identity.Id
            }
            $Suffixes = @("_$i") + @(if ($i -eq 0) { '' })
            foreach ($Suffix in $Suffixes) {
                foreach ($Name in $Values.Keys) {
                    if ($ConfigTarget -eq 'powershell') {
                        Add-Content -Path $OutFile -Value "`$env:$Name$Suffix = `"$($Values[$Name])`""
                    } else {
                        Add-Content -Path $OutFile -Value "export $Name$Suffix=`"$($Values[$Name])`""
                    }
                }
            }
            Write-Host "Emitted X.509 group bootstrap identity $i`: $($Identity.Id)"
        }
    }

    return $TestEnvInfo
}
