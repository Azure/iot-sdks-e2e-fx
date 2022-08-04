# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

set -e

cd /sdk
pip install --upgrade pip
# Temporarily commenting this out because of a structure change in the repo.
# Once Python PR 1030 makes it into main, we can add this back in for a slight improvement
# in image usage. This is because prebuild.sh populates the base docker image (including pip depenencies)
# and rebuild.sh populates the image layers that change for every run. With this commented out, dependencies
# go into per-build layers. When we add this back in, dependencies will go back into the base layers
# that get re-used over and over again. Image size is still the same in both cases.  The only difference
# is in the size of the per-build layers which end up taking more space in the container repository.
# pip install -U --upgrade-strategy eager -e . --ignore-installed packaging
cd /wrapper
pip install -r requirements.txt

