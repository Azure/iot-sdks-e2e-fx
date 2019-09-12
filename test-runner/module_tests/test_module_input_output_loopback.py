# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections
import random
import time
import test_utilities
from adapters import print_message as log_message

output_name = "loopout"
input_name = "loopin"
receive_timeout = 60


@pytest.mark.testgroup_edgehub_module_client
@pytest.mark.callsendOutputMessage
@pytest.mark.receivesInputMessages
@pytest.mark.handlesLoopbackMessages
def test_module_input_output_loopback(test_string):

    module_client = connections.connect_test_module_client()
    module_client.enable_input_messages()

    input_thread = module_client.wait_for_input_event_async(input_name)

    module_client.send_output_event(output_name, test_string)

    received_message = input_thread.get(receive_timeout)
    log_message("input message arrived")
    log_message("expected message: " + str(test_string))
    log_message("received message: " + str(received_message))
    assert received_message == test_string

    module_client.disconnect()
