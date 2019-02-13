# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

function usage {
  echo ""
  echo "To build from commit ID:"
  echo "  $0 --language [lang] --repo [repo] --commit [commit ID]"
  echo "  example: $0 --language node --repo Azure/azure-iot-sdk-node --commit bugfix-branch"
  echo ""
}

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --language)
      export LANGUAGE=$2
      shift ; shift
      ;;
    --commit)
      export COMMIT_ID=$2
      shift ; shift
      ;;
    --repo)
      export AZURE_REPO=$2
      shift ; shift
      ;;
    *)
      echo "unkonwn parameter: $1"
      usage
      exit 1
      ;;
  esac
done

if [ -z ${LANGUAGE} ] ||
   [ -z ${COMMIT_ID} ] ||
   [ -z ${AZURE_REPO} ]; then 
  echo "required parameter missing"
  usage
  exit 1
fi



