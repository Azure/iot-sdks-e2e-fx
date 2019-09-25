# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import functools
import asyncio

from .print_message import print_message


def log_entry_and_exit(_func=None, *, print_args=True):
    """Print the function signature and return value"""

    def decorator_log_entry_and_exit(func):
        @functools.wraps(func)
        def wrapper_log_entry_and_exit(*args, **kwargs):
            if print_args:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
            else:
                if len(args) > 0:
                    signature = repr(args[0]) + ",__ARGUMENTS_REDACTED__"
                else:
                    signature = "__ARGUMENTS_REDACTED__"
            if "__self__" in dir(func):
                func_name = func.__self__.__class__.__name__ + "." + func.__name__
            elif len(args) > 0:
                func_name = args[0].__class__.__name__ + "." + func.__name__
            else:
                func_name = func.__name__
            print_message(f"Callng {func_name!r}({signature})")
            value = func(*args, **kwargs)
            print_message(f"{func_name!r} returned {value!r}")
            return value

        return wrapper_log_entry_and_exit

    if _func is None:
        return decorator_log_entry_and_exit
    else:
        return decorator_log_entry_and_exit(_func)


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
    """Returns a coroutine function that calls a given function with emulated asynchronous
    behavior via use of mulithreading.

    Can be applied as a decorator.

    :param fn: The sync function to be run in async.
    :returns: A coroutine function that will call the given sync function.
    """

    @functools.wraps(fn)
    async def async_fn_wrapper(*args, **kwargs):
        loop = get_running_loop()

        # Run fn in default ThreadPoolExecutor (CPU * 5 threads)
        return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))

    return async_fn_wrapper
