# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license tagsrmation.
import os


def get_default_variant(language):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    language_directory = os.path.normpath(
        os.path.join(script_dir, "../../docker_images/" + language)
    )
    if not os.path.isdir(language_directory):
        raise Exception("path " + language_directory + " does note exist.")
    default_file = os.path.join(language_directory, "default.txt")
    if os.path.isfile(default_file):
        with open(default_file, mode="rt") as f:
            return f.readline().strip()
    else:
        return None
