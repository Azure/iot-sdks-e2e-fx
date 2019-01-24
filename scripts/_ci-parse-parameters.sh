# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

function usage {
  echo ""
  echo "To build from pull request:"
  echo "  $0 --language [lang] --repo [repo] --branch [branch] --prid [pull request id]"
  echo "  example: $0 --language node --repo Azure/azure-iot-sdk-node --branch master --prid 346"
  echo ""
  echo "To build from commit ID:"
  echo "  $0 --language [lang] --repo [repo] --branch [branch] --commit [commit ID]"
  echo "  example: $0 --language node --repo Azure/azure-iot-sdk-node --branch master --commit bugfix-branch"
  echo ""
}

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --language)
      export LANGUAGE=$2
      shift ; shift
      ;;
    --prid)
      export BUILD_WITH_PRID=YES
      export COMMIT_ID=$2
      shift ; shift
      ;;
    --commit)
      export BUILD_WITH_PRID=NO
      export COMMIT_ID=$2
      shift ; shift
      ;;
    --repo)
      export AZURE_REPO=$2
      shift ; shift
      ;;
    --branch)
      export BRANCH_TO_MERGE_TO=$2
      shift ; shift
      ;;
    --forced_image)
      export FORCED_IMAGE=$2
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
   [ -z ${BUILD_WITH_PRID} ] ||
   [ -z ${COMMIT_ID} ] ||
   [ -z ${AZURE_REPO} ] ||
   [ -z ${BRANCH_TO_MERGE_TO} ]; then
  echo "required parameter missing"
  usage
  exit 1
fi



