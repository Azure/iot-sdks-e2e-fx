# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk
[ $? -eq 0 ] || { echo "cd sdk failed"; exit 1; }

mvn -s /usr/share/maven/ref/settings-docker.xml -Dmaven.test.skip=true -Dmaven.javadoc.skip=true -pl :iot-edge-e2e-wrapper  install
[ $? -eq 0 ] || { echo "build sdk failed"; exit 1; }

