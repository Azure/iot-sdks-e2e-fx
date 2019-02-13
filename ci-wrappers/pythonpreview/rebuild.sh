# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk
[ $? -eq 0 ] || { echo "cd sdk failed "; exit 1; }

python env_setup.py --no_dev
[ $? -eq 0 ] || { echo "env_setup.py failed "; exit 1; }
