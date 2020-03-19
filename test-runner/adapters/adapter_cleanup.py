# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from . import rest
from . import direct_azure_rest

try:
    from . import python_inproc
except ModuleNotFoundError:
    # It's OK to fail this.  The import will only succeed if the use has the
    # iot sdks pip packages installed, and the import is only necessary if
    # you're actually using the pp_direct adapters.
    print("Failed to load python_inproc adapters.  Skipping.")
    python_inproc = None


def cleanup_test_objects():
    """
    Function to call into all adapter objects and perform cleanup on the test objects
    that those adapters are responsible for.
    """
    rest.cleanup_test_objects()
    direct_azure_rest.cleanup_test_objects()
    if python_inproc:
        python_inproc.cleanup_test_objects()
