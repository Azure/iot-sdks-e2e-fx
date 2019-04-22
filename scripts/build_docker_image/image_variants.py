# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license tagsrmation.
import os


def get_default_variant(dockerfile_path):
    if not os.path.isdir(dockerfile_path):
        raise Exception("path " + dockerfile_path + " does note exist.")
    default_file = os.path.join(dockerfile_path, "default.txt")
    if os.path.isfile(default_file):
        with open(default_file, mode="rt") as f:
            return f.readline().strip()
    else:
        return None
