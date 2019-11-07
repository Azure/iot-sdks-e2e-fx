# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from . import rest
from . import direct_azure_rest

try:
    from . import direct_python_sdk
except ModuleNotFoundError:
    # It's OK to fail this.  The import will only succeed if the use has the
    # iot sdks pip packages installed, and the import is only necessary if
    # you're actually using the pp_direct adapters.
    print("Failed to load direct_python_sdk adapters.  Skipping.")
    direct_python_sdk = None


def cleanup_test_objects():
    """
    Function to call into all adapter objects and perform cleanup on the test objects
    that those adapters are responsible for.
    """
    rest.cleanup_test_objects()
    direct_azure_rest.cleanup_test_objects()
    if direct_python_sdk:
        direct_python_sdk.cleanup_test_objects()
