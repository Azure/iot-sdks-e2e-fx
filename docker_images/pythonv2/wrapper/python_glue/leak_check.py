# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import gc
import inspect
import os
import weakref
import time
import logging
import importlib

logger = logging.getLogger(__name__)


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


def _dump_referrers(obj):
    referrers = gc.get_referrers(obj.weakref())
    for referrer in referrers:
        if isinstance(referrer, dict):
            print("  dict: {}".format(referrer))
            for sub_referrer in gc.get_referrers(referrer):
                if sub_referrer != referrers:
                    print("    used by: {}:{}".format(type(sub_referrer), sub_referrer))
        elif not isinstance(referrer, type):
            print("  used by: {}:{}".format(type(referrer), referrer))


class LeakedObject(object):
    """
    Object holding details on the leak of some tracked object
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


class TrackedModule(object):
    def __init__(self, module_name):
        self.module_name = module_name
        mod = importlib.import_module(module_name)
        self.path = os.path.dirname(inspect.getsourcefile(mod))

    def is_module_object(self, obj):
        if not isinstance(obj, BaseException):
            try:
                c = obj.__class__
                source_file = inspect.getsourcefile(c)
            except (TypeError, AttributeError):
                pass
            else:
                if source_file and source_file.startswith(self.path):
                    return True

        return False


class LeakTracker(object):
    def __init__(self):
        self.tracked_modules = []
        self.previous_leaks = []

    def add_tracked_module(self, module_name):
        self.tracked_modules.append(TrackedModule(module_name))

    def _get_all_tracked_objects(self):
        """
        Query the garbage collector for a a list of all objects that
        are implemented in tracked libraries
        """
        all = []
        for obj in gc.get_objects():
            if any([mod.is_module_object(obj) for mod in self.tracked_modules]):
                source_file = inspect.getsourcefile(obj.__class__)
                try:
                    all.append(LeakedObject(source_file, obj))
                except TypeError:
                    logger.warning(
                        "Could not add {} from {} to leak list".format(
                            obj.__class__, source_file
                        )
                    )
        return all

    def _prune_previous_leaks_list(self):
        """
        remove objects from our list of previous leaks if they've been collected
        """

        new_previous_leaks = []
        for obj in self.previous_leaks:
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
                len(self.previous_leaks), len(new_previous_leaks)
            )
        )
        self.previous_leaks = new_previous_leaks

    def _filter_previous_leaks(self, all):
        """
        Return a filtered leak list where all previously reported leaks have been removed.
        """

        self._prune_previous_leaks_list()

        new_list = []
        for obj in all:
            if obj not in self.previous_leaks:
                new_list.append(obj)
            else:
                logger.info("Object {} previously reported".format(obj))

        logger.info(
            "active list pruned from {} items to {} items".format(
                len(all), len(new_list)
            )
        )

        return new_list

    def set_baseline(self):
        self.previous_leaks = self._get_all_tracked_objects()

    def check_for_new_leaks(self):
        """
        Get all tracked objects from the garbage collector.  If any objects remain, list
        them and assert so the test fails.
        """
        _run_garbage_collection()

        all_tracked_objects = self._get_all_tracked_objects()
        all_tracked_objects = self._filter_previous_leaks(all_tracked_objects)
        if len(all_tracked_objects):
            logger.error(
                "Test failure.  {} objects have leaked:".format(
                    len(all_tracked_objects)
                )
            )
            for obj in all_tracked_objects:
                logger.error("LEAK: {}".format(obj))
                _dump_referrers(obj)
                self.previous_leaks.append(obj)
            assert False
        else:
            logger.info("No leaks")
