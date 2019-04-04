#!/usr/bin/env python
import asyncio

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

loop = None


def get_event_loop():
    global loop

    try:
        existing_loop = asyncio.get_event_loop()
    except RuntimeError:
        existing_loop = None

    if not loop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    elif existing_loop != loop:
        asyncio.set_event_loop(loop)

    return loop
