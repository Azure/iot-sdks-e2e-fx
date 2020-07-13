# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import json
import datetime
import re
import threading
import inflection


class SimpleObject(object):
    def __init__(self):
        self._attributes_locked = False
        self._lock = threading.Lock()

    def _get_attribute_names(self):
        """
        return all public attribute names for this object.  Excludes all callables and all
        attributes that start wth an underscore.
        """
        return [
            i
            for i in dir(self)
            if not i.startswith("_") and not callable(getattr(self, i))
        ]

    def lock_attributes(self):
        """
        Lock attributes.  When an object has its attributes locked, you can't add any dynamic
        attributes to the object.
        """
        self._attributes_locked = True
        for name in self._get_attribute_names():
            sub = getattr(self, name)
            if isinstance(sub, SimpleObject):
                sub.lock_attributes()

    def __setattr__(self, name, value):
        if (
            hasattr(self, name)
            or not hasattr(self, "_attributes_locked")
            or not self._attributes_locked
        ):
            super(SimpleObject, self).__setattr__(name, value)
        else:
            raise AttributeError(
                "attribute {} does not exist on {}".format(name, type(self))
            )


class DictionaryObject(SimpleObject):
    @classmethod
    def from_dict(cls, dict_object):
        """
        convert a dictionary to a native object of this type
        """
        native_object = cls()
        native_object.fill_from_dict(dict_object)
        return native_object

    @classmethod
    def from_file(cls, filename):
        """
        read a file containing a dict in json format and convert it into a native object of this type
        """
        with open(filename) as json_file:
            dict_object = json.load(json_file)

        return cls.from_dict(dict_object)

    def fill_from_dict(self, dict_object):
        """
        Fill an object with data in a dictionary
        """

        def fill_native_object_from_dict(native_object, dict_object):
            for dict_key in dict_object:
                native_key = inflection.underscore(dict_key)
                dict_value = dict_object[dict_key]
                if isinstance(dict_value, dict):
                    native_value = getattr(native_object, native_key, SimpleObject())
                    setattr(native_object, native_key, native_value)
                    fill_native_object_from_dict(native_value, dict_value)
                elif _is_scalar(dict_value):
                    old_native_value = getattr(native_object, native_key, None)
                    if _is_tostring_object(old_native_value):
                        _set_tostring_attr(native_object, native_key, dict_value)
                    else:
                        setattr(native_object, native_key, dict_value)
                else:
                    raise ValueError(
                        "{} must be a dictionary, string, or scalar value".format(
                            dict_key
                        )
                    )

        fill_native_object_from_dict(self, dict_object)

    def fill_from_file(self, filename):
        """
        Read a file with JSON and fill this object with the data in the file
        """
        with open(filename) as json_file:
            dict_object = json.load(json_file)

        self.fill_from_dict(dict_object)

    def to_dict(self, defaults=None):
        """
        convert this object to a dict
        """

        try:
            defaults = defaults or type(self)._defaults
        except AttributeError:
            pass

        def dict_from_native_object(native_object, default_object):
            dict_object = {}
            for native_key in native_object._get_attribute_names():
                dict_key = inflection.camelize(native_key, uppercase_first_letter=False)

                default_value = None
                if default_object:
                    default_value = getattr(default_object, native_key, None)

                native_value = getattr(native_object, native_key)

                if _is_scalar(native_value):
                    # always include None, even if it's the default.  This is
                    # because None has a special meaning if we're using this to send a
                    # twin patch.
                    if (default_value is None) or (native_value != default_value):
                        dict_object[dict_key] = native_value
                elif _is_tostring_object(native_value):
                    if native_value != default_value:
                        dict_object[dict_key] = str(native_value)
                elif isinstance(native_value, object):
                    new_value = dict_from_native_object(native_value, default_value)
                    if new_value:
                        dict_object[dict_key] = new_value
                else:
                    raise ValueError(
                        "{} must be a scalar value or an object".format(native_key)
                    )
            return dict_object

        return dict_from_native_object(self, defaults)

    def to_file(self, filename):
        """
        convert this object into a dict and sve it to a file
        """
        dict_object = self.to_dict()

        with open(filename, "w") as outfile:
            json.dump(dict_object, outfile, indent=2)


def _is_tostring_object(x):
    return type(x) in [datetime.timedelta, datetime.datetime]


def _is_scalar(x):
    return type(x) in [int, bool, str, type(None), float]


def _set_tostring_attr(obj, key, value):
    old_value = getattr(obj, key)
    if type(old_value) == datetime.timedelta:
        setattr(obj, key, string_to_timedelta(value))
    elif type(old_value) == datetime.datetime:
        setattr(obj, key, datetime.datetime.fromisoformat(value))
    else:
        raise ValueError()


def string_to_timedelta(s):
    # https://stackoverflow.com/a/21074460
    if "day" in s:
        m = re.match(
            r"(?P<days>[-\d]+) day[s]*, (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)",
            s,
        )
    else:
        m = re.match(r"(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)", s)
    d = {key: float(m.groupdict()[key]) for key in m.groupdict()}

    return datetime.timedelta(**d)
