# AzIotSdkTest

Shared end-to-end test framework for the Azure IoT SDKs: provisions IoT Hub /
DPS test environments, emits per-SDK test configuration, and checks submodule
consistency.

## Layout

| Path | Contents |
| --- | --- |
| `AzIotSdkTest.psd1` | Manifest. `ModuleVersion` and the exported surface. |
| `AzIotSdkTest.psm1` | Root module. Dot-sources `Import-Parts.ps1`. |
| `Import-Parts.ps1` | Load order and `Export-ModuleMember` declarations. |
| `parts/*.ps1` | The implementation. |

`Import-Parts.ps1` is a separate `.ps1` because the deprecated
`../Azure.Iot.Sdk.Test.psm1` shim dot-sources the same loader, and PowerShell's
dot-source operator accepts only `.ps1`.

**The load order in `$ModuleParts` is significant.** PowerShell resolves a class
used as a parameter type when the file declaring the consumer is parsed, so
`Models.ps1` must load before anything that takes a `[TestEnvironmentInfo]`.
`tests/Validate-Module.ps1` fails the build if a file in `parts/` is missing from
the list -- it would otherwise load as nothing at all -- or if the list names a
file that is not there.

## Importing it

Import the **manifest**, not a `.psm1`:

```powershell
Import-Module <checkout>/scripts/AzIotSdkTest/AzIotSdkTest.psd1
```

Consumers should get the checkout from the ref they pinned, rather than
downloading the module:

* GitHub Actions: `uses: Azure/iot-sdks-e2e-fx/actions/<action>@<tag>`
* Azure Pipelines: a `repositories` resource plus `- template: ...@e2e_fx`
  (see [actions/README.md](../../actions/README.md#azure-pipelines))

Both give the runner this repository at a pinned ref, so the module cannot drift
away from the pipeline that calls it. Both end in `New-AzIotE2ETestEnvironmentAndConfig`, which
provisions an environment and writes its test configuration.

`../Azure.Iot.Sdk.Test.psm1` still works, and is deprecated. It exists for
pipelines that download that one file from `raw.githubusercontent.com`; when
imported from a checkout it dot-sources this module, and when imported standalone
it downloads the repository (defaulting to `master`, which is what those
pipelines already get today). Move those callers to a pinned checkout; the shim
will be removed afterwards.

## Permanent test environments

Pipelines create an environment per run and delete it afterwards. A
long-lived environment that pull request runs share is created once, by a
person, with `-Permanent`:

```powershell
New-AzIotTestEnvironment -ResourceGroup <name> -Permanent -DisableLocalAuth `
    -IotHubUnits 2 -DataPlaneServicePrincipalIds <ci-principal-object-id>
```

`New-AzIotMqttv5TestEnvironment` takes the same three parameters.

* The resource group is tagged `AzIotSdkTestPermanent=true`, and
  `Remove-LeftoverAzureResourceGroups` never deletes or stamps a tagged group,
  whatever `-Prefix` it runs with.
* The name must not start with the default cleanup prefix
  (`rg-iot-sdk-e2e-`), so an untagged copy is not deleted either.
* `-DataPlaneServicePrincipalIds` grants the CI identities IoT Hub Data
  Contributor on the hub and, with `-RouteTelemetryToEventHub`, Azure Event Hubs
  Data Receiver on the telemetry Event Hub.
* The functions create resources; they do not update existing ones. To rebuild
  an environment, delete the resource group or use a new name.

## Windows PowerShell 5.1

The module must stay 5.1-compatible: `vsts/templates/steps-create-azure-resources.yaml`
runs `AzureCLI@2` with `scriptType: ps`, which is Windows PowerShell, not pwsh.
In practice that rules out things like three-argument `Join-Path`, ternaries and
`??`.

## Checks

```bash
pwsh -NoProfile -File tests/Validate-Module.ps1
```

Parses every part, verifies the load order covers `parts/` exactly, imports the
module and asserts the exported command set matches the declared contract and the
manifest, and confirms the deprecated shim still yields the same commands. It
provisions nothing and needs no credentials.

## Versioning

Bump `ModuleVersion` on any change a consumer can observe, and tag the
repository; consumers pin that tag. A pipeline log should be able to name the
version that provisioned a run.
