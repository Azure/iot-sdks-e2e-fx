> [!NOTE]
> These actions are the GitHub Actions face of the Azure Pipelines step
> templates in [`vsts/templates/`](../vsts/templates). Both call the same
> `AzIotSdkTest` module in [`scripts/AzIotSdkTest/`](../scripts/AzIotSdkTest). Keep the logic in the
> module; keep these files thin.

# Composite actions

| Action | Azure Pipelines equivalent |
| --- | --- |
| [`provision-e2e-resources`](provision-e2e-resources) | `vsts/templates/steps-create-azure-resources.yaml` |
| [`destroy-e2e-resources`](destroy-e2e-resources) | `vsts/templates/steps-destroy-azure-resources.yaml` |
| [`check-submodules`](check-submodules) | `Test-SubmoduleConsistency`, called directly |

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

## Conventions these actions follow

* **Inputs reach the script through `env:`, never through `${{ }}`
  interpolation into the script body.** An input is data; interpolation would
  make it code. `tests/validate-actions.mjs` fails the build on any expression
  found inside a script body.
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
