# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

language=$1
tag=$2

function usage {
    echo "Usage: $0 [node | c | csharp | java | pythonv2] [tag]"
    echo "eg: $0 pythonv2 vsts-12345"
}

if [ "$language" == "" ] || [ "$tag" == "" ]; then
    usage
    exit 1
fi

case "$language" in
  node | c | csharp | java | pythonv2)
    echo "tagging ${language} ${tag} as LKG"
    ;;
  *)
    usage
    exit 1
    ;;
esac

variants=""
case "$language" in
  node)
    variants="node6 node8 node10"
    ;;
  pythonv2)
    variants="py27 py34 py35 py36 py37 py38"
    ;;
esac

base=${IOTHUB_E2E_REPO_ADDRESS}/${language}-e2e-v3

docker login -u ${IOTHUB_E2E_REPO_USER} -p ${IOTHUB_E2E_REPO_PASSWORD} ${IOTHUB_E2E_REPO_ADDRESS}
[ $? -eq 0 ] || { echo "docker login failed"; exit 1; }

docker pull ${base}:${tag}
[ $? -eq 0 ] || { echo "docker pull ${base}:${tag} failed"; exit 1; }

docker tag ${base}:${tag} ${base}:lkg
[ $? -eq 0 ] || { echo "docker tag ${base}:${tag} ${base}:lkg failed"; exit 1; }

docker push ${base}:lkg
[ $? -eq 0 ] || { echo "docker push ${base}:lkg failed"; exit 1; }

for variant in ${variants}; do
    docker pull ${base}:${tag}-${variant}
    [ $? -eq 0 ] || { echo "docker pull ${base}:${tag}-${variant} failed"; exit 1; }

    docker tag ${base}:${tag}-${variant} ${base}:lkg-${variant}
    [ $? -eq 0 ] || { echo "docker tag ${base}:${tag}-${variant} ${base}:lkg-${variant} failed"; exit 1; }

    docker push ${base}:lkg-${variant}
    [ $? -eq 0 ] || { echo "docker push ${base}:lkg failed"; exit 1; }
done

