# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import asyncio
import threading
import logging
import inspect

logger = logging.getLogger(__name__)

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


def wrap_coroutine(coroutine):
    def wrapper(*args, **kwargs):
        result = None
        error = None

        done = threading.Event()

        async def wrapped_coroutine():
            logger.info("inside wrapped_corountine")
            nonlocal result
            nonlocal error
            try:
                result = await coroutine(*args, **kwargs)
            except Exception as e:
                error = e
            done.set()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), loop=get_event_loop())
        done.wait()
        if error:
            raise error
        return result

    return wrapper


def wrap_object(obj):
    for name in dir(obj):
        member = getattr(obj, name)
        print(
            "{} {} {}".format(
                name, inspect.ismethod(member), inspect.iscoroutinefunction(member)
            )
        )
        if (
            not name.startswith("_")
            and not name.endswith("_sync")
            and inspect.ismethod(member)
            and inspect.iscoroutinefunction(member)
        ):
            newname = name + "_sync"
            logger.info("wrapping {} to become {}".format(name, newname))
            setattr(obj, newname, wrap_coroutine(member))
