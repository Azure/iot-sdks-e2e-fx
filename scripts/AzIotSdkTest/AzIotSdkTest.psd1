@{
    RootModule        = 'AzIotSdkTest.psm1'

    # Bump on every change that consumers can observe. Consumers pin a TAG of
    # this repository, not a branch; this version is what a pipeline log should
    # name when someone asks which code provisioned a run.
    ModuleVersion     = '1.0.0'

    GUID              = 'b0f3b0b6-6a2f-4b1e-9d7a-8f3f1a6c2d55'
    Author            = 'Microsoft Corporation'
    CompanyName       = 'Microsoft Corporation'
    Copyright         = '(c) Microsoft Corporation. All rights reserved.'
    Description       = 'Shared end-to-end test framework for the Azure IoT SDKs: provisions IoT Hub/DPS test environments, emits per-SDK test configuration, and checks submodule consistency.'

    # Windows PowerShell 5.1 is still in use: the Azure Pipelines templates in
    # this repository run AzureCLI@2 with scriptType 'ps', which is Windows
    # PowerShell, not pwsh. Keep the module 5.1-compatible.
    PowerShellVersion = '5.1'

    FunctionsToExport = @(
        'Debug-PSScript'
        'Invoke-Script'
        'Set-FileContent'
        'Get-AzureResourceGroupNamePrefix'
        'New-AzureResourceGroupName'
        'Remove-LeftoverAzureResourceGroups'
        'New-AzIotTestEnvironment'
        'Get-AzIotTestEnvironment'
        'ConvertFrom-JsonToTestEnvironmentInfo'
        'New-AzIotCSDKE2ETestConfig'
        'New-AzIotNetSDKE2ETestConfig'
        'New-AzIotPythonSDKE2ETestConfig'
        'New-AzIotPythonSdkSampleConfig'
        'New-AzIotuAmqpE2ETestConfig'
        'New-AzIotHortonTestConfig'
        'Test-SubmoduleConsistency'
    )

    CmdletsToExport   = @()
    VariablesToExport = @()
    AliasesToExport   = @()

    PrivateData       = @{
        PSData = @{
            Tags       = @('Azure', 'IoT', 'E2E', 'Test')
            ProjectUri = 'https://github.com/Azure/iot-sdks-e2e-fx'
            LicenseUri = 'https://github.com/Azure/iot-sdks-e2e-fx/blob/master/LICENSE'
        }
    }
}
