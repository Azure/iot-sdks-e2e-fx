# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import asyncio
import logging
import inspect
import functools
import concurrent.futures

logger = logging.getLogger(__name__)

# default executor is not sufficient since default threads == CPUx5 and
# VMs will default to 1 CPU.
try:
    emulate_async_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=32, thread_name_prefix="emulate_async"
    )
except TypeError:
    # for py35
    emulate_async_executor = concurrent.futures.ThreadPoolExecutor(max_workers=32)


def get_running_loop():
    """
    Gets the currently running event loop

    Uses asyncio.get_running_loop() if available (Python 3.7+) or a backported
    version of the same function in 3.5/3.6.
    """
    try:
        loop = asyncio.get_running_loop()
    except AttributeError:
        loop = asyncio._get_running_loop()
        if loop is None:
            raise RuntimeError("no running event loop")
    return loop


def emulate_async(fn):
    """
    Returns a coroutine function that calls a given function with emulated asynchronous
    behavior via use of mulithreading.

    Can be applied as a decorator.

    :param fn: The sync function to be run in async.
    :returns: A coroutine function that will call the given sync function.
    """

    @functools.wraps(fn)
    async def async_fn_wrapper(*args, **kwargs):
        loop = get_running_loop()

        return await loop.run_in_executor(
            emulate_async_executor, functools.partial(fn, *args, **kwargs)
        )

    return async_fn_wrapper


def wrap_object(obj):
    for name in dir(obj):
        member = getattr(obj, name)
        if (
            not name.startswith("_")
            and name.endswith("_sync")
            and inspect.ismethod(member)
        ):
            newname = name[:-5]
            logger.info("wrapping {} to become {}".format(name, newname))
            setattr(obj, newname, emulate_async(member))
