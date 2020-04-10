# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import gc
import inspect
import os
import azure.iot.device as iothub_library_root
import weakref
import time
import logging
import _ctypes
from six import string_types, types

logger = logging.getLogger(__name__)

iothub_library_root_path = os.path.dirname(inspect.getsourcefile(iothub_library_root))
iothub_library_root_path_len = len(iothub_library_root_path) + 1


class LeakedObject(object):
    """
    Object holding details on the leak of some IoTHub client object
    """

    def __init__(self, source_file, obj):
        self.source_file = source_file
        self.value = str(obj)
        self.weakref = weakref.ref(obj)

    def __repr__(self):
        return "{}-{}".format(self.source_file, self.value)

    def __eq__(self, obj):
        return self.source_file == obj.source_file and self.weakref == obj.weakref

    def __ne__(self, obj):
        return not self == obj


def _is_paho_object(obj):
    if not isinstance(obj, BaseException):
        try:
            c = obj.__class__
            source_file = inspect.getsourcefile(c)
        except (TypeError, AttributeError):
            pass
        else:
            if source_file and "paho" in source_file:
                return True
    return False


def _is_iothub_object(obj):
    if not isinstance(obj, BaseException):
        try:
            c = obj.__class__
            source_file = inspect.getsourcefile(c)
        except (TypeError, AttributeError):
            pass
        else:
            if source_file and source_file.startswith(iothub_library_root_path):
                return True
    return False


def get_all_iothub_objects():
    """
    Query the garbage collector for a a list of all objects that
    are implemented in an iothub library.
    """
    all = []
    for obj in gc.get_objects():
        if _is_iothub_object(obj) or _is_paho_object(obj):
            source_file = inspect.getsourcefile(obj.__class__)
            if _is_iothub_object(obj):
                source_file = source_file[iothub_library_root_path_len:]
            try:
                all.append(LeakedObject(source_file, obj))
            except TypeError:
                logger.warning(
                    "Could not add {} from {} to leak list".format(
                        obj.__class__, source_file
                    )
                )
    return all


def _free_all(objs):
    """
    Free all objects in a list of LeakObjects.  This is done in order to attempt
    recovery for future tests.  Otherwise, a leak in one test will show up as a leak
    in all subsequent tests.

    Note: this can only clean up internally referenced objects.  If something outside
    of our library is holding a reference on a library object, this won't free it.
    """
    for obj in objs:
        o = obj.weakref()
        if o and getattr(o, "__dict__", None):
            for attr in o.__dict__:
                setattr(o, attr, None)


def _dump_referrers(obj):
    referrers = gc.get_referrers(obj.weakref())
    for referrer in referrers:
        if isinstance(referrer, dict):
            for sub_referrer in gc.get_referrers(referrer):
                if sub_referrer != referrers:
                    print("  used by: {}:{}".format(type(sub_referrer), sub_referrer))
        elif not isinstance(referrer, type):
            print("  used by: {}:{}".format(type(referrer), referrer))


def _dump_leaked_object(obj):
    logger.error("LEAK: {}".format(obj))

    _dump_referrers(obj)


def _run_garbage_collection():
    """
    Collect everything until there's nothing more to collect
    """
    sleep_time = 2
    done = False
    while not done:
        collected = gc.collect(2)
        logger.info("{} objects collected".format(collected))
        if collected:
            logger.info("Sleeping for {} seconds".format(sleep_time))
            time.sleep(sleep_time)
        else:
            done = True


previous_leaks = []


def _prune_previous_leaks_list():
    global previous_leaks
    new_previous_leaks = []
    for obj in previous_leaks:
        if obj.weakref():
            new_previous_leaks.append(obj)
        else:
            logger.info(
                "Object {} collected since last test.  Removing from previous_leaks list.".format(
                    obj
                )
            )
    logger.info(
        "previous leaks pruned from {} items to {} items".format(
            len(previous_leaks), len(new_previous_leaks)
        )
    )
    previous_leaks = new_previous_leaks


def _remove_previous_leaks_from_list(all):
    global previous_leaks

    _prune_previous_leaks_list()

    new_list = []
    for obj in all:
        if obj not in previous_leaks:
            new_list.append(obj)
        else:
            logger.info("Object {} previously reported".format(obj))

    logger.info(
        "active list pruned from {} items to {} items".format(len(all), len(new_list))
    )
    return new_list


def assert_all_iothub_objects_have_been_collected():
    """
    Get all iothub objects from the garbage collector.  If any objects remain, list
    them and assert so the test fails.  Finally, attempt to clean up leaks so that
    future tests in this session have a clean slate (or as clean as we can make it).
    """
    global previous_leaks

    _run_garbage_collection()

    all_iothub_objects = get_all_iothub_objects()
    all_iothub_objects = _remove_previous_leaks_from_list(all_iothub_objects)
    if len(all_iothub_objects):
        logger.error(
            "Test failure.  {} objects have leaked:".format(len(all_iothub_objects))
        )
        for obj in all_iothub_objects:
            _dump_leaked_object(obj)
            previous_leaks.append(obj)
        _free_all(all_iothub_objects)
        assert False
    else:
        logger.info("No leaks")
