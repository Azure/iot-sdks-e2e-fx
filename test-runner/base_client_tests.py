# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import connections


class BaseClientTests(object):
    @pytest.mark.it("Can connect and immediately disconnect")
    def test_client_connect_disconnect(self, client):
        pass
