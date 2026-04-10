function New-AzIotHortonTestConfig {
    <#
    .SYNOPSIS
    Creates a Horton test configuration script with the environment variables needed by the Horton test framework.

    .DESCRIPTION
    Generates a bash or PowerShell script that exports the environment variables required by Horton,
    including the IoT Hub connection string and Azure Container Registry credentials.

    .PARAMETER TestEnvInfo
    The TestEnvironmentInfo object returned by New-AzIotTestEnvironment (with -AddContainerRegistry).

    .PARAMETER Target
    The target script format: 'bash' or 'powershell'. Default is 'bash'.

    .PARAMETER OutFile
    The output file path. If not specified, a default name is used.

    .EXAMPLE
    PS> $TestEnvInfo = New-AzIotTestEnvironment -NoDps -AddContainerRegistry
    PS> New-AzIotHortonTestConfig -TestEnvInfo $TestEnvInfo -Target bash -OutFile test_config/set_horton_env_vars.sh
    #>
    param(
        $TestEnvInfo = $null,
        [ValidateSet('powershell', 'bash')]
        [string]$Target = "bash",
        [string]$OutFile
    )

    if ([string]::IsNullOrWhiteSpace($OutFile)) {
        $OutFile = "./horton-test-config"
        if ($Target -eq "powershell") {
            $OutFile += ".ps1"
        } else {
            $OutFile += ".sh"
        }
    }

    $AcrLoginServer = $TestEnvInfo.ContainerRegistry[0].LoginServer
    $AcrUsername = $TestEnvInfo.ContainerRegistry[0].Username
    $AcrPassword = $TestEnvInfo.ContainerRegistry[0].Password

    if ($Target -eq "powershell") {
        $Lines = @(
            "`$env:IOTHUB_E2E_CONNECTION_STRING = `"$($TestEnvInfo.IotHub.ConnectionString)`""
            "`$env:IOTHUB_E2E_REPO_ADDRESS = `"$AcrLoginServer`""
            "`$env:IOTHUB_E2E_REPO_USER = `"$AcrUsername`""
            "`$env:IOTHUB_E2E_REPO_PASSWORD = `"$AcrPassword`""
            "`$env:AZURE_RESOURCE_GROUP = `"$($TestEnvInfo.AzureResourceGroup)`""
        )
    } else { # bash
        $Lines = @(
            "#!/bin/bash"
            "export IOTHUB_E2E_CONNECTION_STRING=`"$($TestEnvInfo.IotHub.ConnectionString)`""
            "export IOTHUB_E2E_REPO_ADDRESS=`"$AcrLoginServer`""
            "export IOTHUB_E2E_REPO_USER=`"$AcrUsername`""
            "export IOTHUB_E2E_REPO_PASSWORD=`"$AcrPassword`""
            "export AZURE_RESOURCE_GROUP=`"$($TestEnvInfo.AzureResourceGroup)`""
        )
    }

    $Content = $($Lines -join "`n") + "`n"

    Set-FileContent -Path "$OutFile" -Content "$Content"

    Write-Host "Horton test configuration written to $OutFile"

    return $OutFile
}
