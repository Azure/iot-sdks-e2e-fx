# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import gc
import inspect
import os
import azure.iot.device as library_root
import weakref
import time
import logging

logger = logging.getLogger(__name__)

library_root_path = os.path.dirname(inspect.getsourcefile(library_root))
library_root_path_len = len(library_root_path) + 1


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


def get_all_iothub_objects():
    """
    Query the garbage collector for a a list of all objects that
    are implemented in an iothub library.
    """
    all = []
    for obj in gc.get_objects():
        if not isinstance(obj, BaseException):
            try:
                c = obj.__class__
                source_file = inspect.getsourcefile(c)
            except (TypeError, AttributeError):
                pass
            else:
                if source_file and source_file.startswith(library_root_path):
                    all.append(LeakedObject(source_file[library_root_path_len:], obj))
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


def assert_all_iothub_objects_have_been_collected():
    """
    Get all iothub objects from the garbage collector.  If any objects remain, list
    them and assert so the test fails.  Finally, attempt to clean up leaks so that
    future tests in this session have a clean slate (or as clean as we can make it).
    """
    pass  # can't run this until python PR 334 accepted
    """
    while gc.collect(2):
        time.sleep(1)
    objs = get_all_iothub_objects()
    if len(objs):
        logger.error("Test failure.  Objects have leaked:")
        for obj in objs:
            logger.error("LEAK: {}".format(obj))
        _free_all(objs)
        assert False
    """
