# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import asyncio
import threading
import logging

logging.getLogger("asyncio").setLevel(logging.DEBUG)
loop = None
loop_thread = None


def get_event_loop():
    global loop
    global loop_thread

    if not loop:
        loop = asyncio.new_event_loop()
        loop_thread = threading.Thread(target=loop.run_forever, daemon=True)
        loop_thread.start()

    try:
        existing_loop = asyncio.get_event_loop()
    except RuntimeError:
        existing_loop = None

    if existing_loop != loop:
        asyncio.set_event_loop(loop)

    return loop


def run_coroutine_sync(coroutine):
    global loop
    result = None

    done = threading.Event()

    async def wrapped_coroutine():
        print("inside wrapped_corountine")
        nonlocal result
        result = await coroutine
        done.set()

    asyncio.run_coroutine_threadsafe(wrapped_coroutine(), loop=get_event_loop())
    done.wait()
    return result
