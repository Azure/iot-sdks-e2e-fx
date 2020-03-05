# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import concurrent.futures
import functools
import asyncio

# default executor is not sufficient since default threads == CPUx5 and
# VMs will default to 1 CPU.
emulate_async_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=32, thread_name_prefix="emulate_async"
)

control_api_emulate_async_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=8, thread_name_prefix="control_api_emulate_async"
)


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


def control_api_emulate_async(fn):
    """
    Returns a coroutine function that calls a given function with emulated asynchronous
    behavior via use of mulithreading.

    Control APIs have their own threadpool.  This is necessary because the emualte_async
    threadpool can become full, especially if the network is disconencted.  We need
    control APIs to run so we can re-connect the network in this scenario.

    Can be applied as a decorator.

    :param fn: The sync function to be run in async.
    :returns: A coroutine function that will call the given sync function.
    """

    @functools.wraps(fn)
    async def async_fn_wrapper(*args, **kwargs):
        loop = get_running_loop()

        return await loop.run_in_executor(
            control_api_emulate_async_executor, functools.partial(fn, *args, **kwargs)
        )

    return async_fn_wrapper
