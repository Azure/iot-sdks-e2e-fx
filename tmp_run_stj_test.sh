#!/bin/bash
set -ex
cd ~/e2e-fx
source test_config/set_horton_env_vars.sh
source bin/_virtualenv/horton/bin/activate

TAG=csharp-e2e-stj:latest

# Skip docker pull for local-only image: comment out pull_docker_image call
sed -i 's/^    utilities.pull_docker_image(test_image)$/    #utilities.pull_docker_image(test_image)/' bin/deploy/horton_deploy.py
# Prevent ACR prefix from being prepended to local image name
unset IOTHUB_E2E_REPO_ADDRESS

echo "=== Deploying ==="
python bin/horton.py undeploy || true
python bin/horton.py deploy iothub image $TAG
python bin/horton.py get_credentials

echo "=== Running IoT Hub tests with mqtt ==="
cd test-runner
python -m pytest --scenario iothub_module --transport=mqtt -x --timeout=300 -v 2>&1
exit_code=$?
echo "=== MQTT EXIT CODE: $exit_code ==="
exit $exit_code
