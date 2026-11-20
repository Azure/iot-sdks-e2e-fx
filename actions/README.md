> [!NOTE]
> These actions are the GitHub Actions face of the Azure Pipelines step
> templates in [`vsts/templates/`](../vsts/templates). Both call the same
> `AzIotSdkTest` module in [`scripts/AzIotSdkTest/`](../scripts/AzIotSdkTest). Keep the logic in the
> module; keep these files thin.

# Composite actions

| Action | Azure Pipelines equivalent |
| --- | --- |
| [`provision-e2e-resources`](provision-e2e-resources) | [`vsts/templates/steps-provision-e2e-resources.yaml`](../vsts/templates/steps-provision-e2e-resources.yaml) |
| [`destroy-e2e-resources`](destroy-e2e-resources) | [`vsts/templates/steps-destroy-e2e-resources.yaml`](../vsts/templates/steps-destroy-e2e-resources.yaml) |
| [`check-submodules`](check-submodules) | `Test-SubmoduleConsistency`, called directly |

`provision-e2e-resources` and its template both call `New-AzIotE2ETestEnvironmentAndConfig`, so
they take the same settings and provision the same environment. Horton's own pipelines use
`steps-create-azure-resources.yaml` and `steps-destroy-azure-resources.yaml`, which are separate.

## Why an action rather than downloading the module

To run one of these, the runner first checks this repository out at the ref the
caller pinned. The module is therefore already on disk, and the action imports it
from its own checkout:

```yaml
env:
  AZ_IOT_MODULE: ${{ github.action_path }}/../../scripts/AzIotSdkTest/AzIotSdkTest.psd1
```

Two consequences worth stating:

* **No download.** There is no `Invoke-WebRequest`, so there is no "HTTP 200,
  stale module" failure mode and no dependency on `raw.githubusercontent.com`.
* **Action and module are the same commit, always.** A caller pinned to `@v1`
  gets the `v1` module. Downloading the module from `master` while pinning the
  caller to anything else is what lets a merge here change another repository's
  pipeline without anyone choosing to take the change.

Pin a tag, not a branch.

## Usage

```yaml
jobs:
  e2e:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # azure/login with OIDC
      contents: read
    steps:
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - id: provision
        uses: Azure/iot-sdks-e2e-fx/actions/provision-e2e-resources@v1
        with:
          # Deterministic, so teardown can find the group even if this job is cancelled.
          rg-name: MyE2E-${{ github.run_id }}-${{ github.run_attempt }}
          config-cmdlet: New-AzIotCSDKE2ETestConfig
          config-target: bash
          out-file: test_config/set_e2e_test_env_vars.sh

      - run: |
          source test_config/set_e2e_test_env_vars.sh
          ./run-my-e2e-tests.sh

      - if: always()
        uses: Azure/iot-sdks-e2e-fx/actions/destroy-e2e-resources@v1
        with:
          resource-group: MyE2E-${{ github.run_id }}-${{ github.run_attempt }}
```

`azure/login` must run in the **caller**: a composite action cannot read
`secrets`.

### Azure Pipelines

```yaml
resources:
  repositories:
    - repository: e2e_fx
      type: github
      name: Azure/iot-sdks-e2e-fx
      ref: refs/tags/v1.3.0
      endpoint: <GitHub service connection>

variables:
  # Deterministic, so teardown needs neither the setup job's outputs nor a checkout.
  e2eResourceGroup: MyE2E-$(Build.BuildId)

jobs:
  - job: setup
    steps:
      - checkout: self
      - checkout: e2e_fx
        path: e2e-fx
      - template: vsts/templates/steps-provision-e2e-resources.yaml@e2e_fx
        parameters:
          azureSubscription: <Azure Resource Manager service connection>
          resourceGroupName: $(e2eResourceGroup)
          enableFileUpload: true
          disableLocalAuth: true
          routeTelemetryToEventHub: true
          telemetryEventHubConsumerGroups: [e2e-0, e2e-1]
          outFile: $(Agent.TempDirectory)/test-config/set_test_env_vars.ps1
          frameworkRoot: $(Agent.BuildDirectory)/e2e-fx

  # ... test jobs ...

  - job: teardown
    dependsOn: [setup]
    condition: and(always(), ne(dependencies.setup.result, 'Skipped'))
    steps:
      - checkout: none
      - template: vsts/templates/steps-destroy-e2e-resources.yaml@e2e_fx
        parameters:
          azureSubscription: <Azure Resource Manager service connection>
          resourceGroupName: $(e2eResourceGroup)
```

The template runs `AzureCLI@2` with `scriptType: pscore`. The test configuration holds secrets:
encrypt it before publishing it as an artifact.

## Conventions these actions follow

* **Inputs reach the script through `env:`, never through `${{ }}`
  interpolation into the script body.** An input is data; interpolation would
  make it code. `tests/validate-actions.mjs` fails the build on any expression
  found inside a script body. The same rules hold for the parameters of the two
  Azure Pipelines templates above.
* **Every declared input is used, and every used input is declared.** GitHub
  silently ignores an unknown key passed in `with:`, so drift here is invisible
  at runtime; the same test fails the build on it.
* **Calls into `AzIotSdkTest` are checked against the module.** The test
  parses each inline script and verifies the cmdlets and parameters exist.

Run the checks locally:

```bash
npm install --no-save js-yaml
node tests/validate-actions.mjs
```
