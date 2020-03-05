# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

# default timeout for all rest API calls, not otherwise specified
default_api_timeout = 120

# timeout for control APIs.  Separated from default_api_timeout because these API
# calls aren't subject to network disconnection
control_api_timeout = 60

# timeout for print_message calls
print_message_timeout = 2

# function that adapters can use to log messages to the output stream
logger = None
