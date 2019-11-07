# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import connection_string
import json


def _can_serialize(obj_name, obj):
    if callable(obj):
        return False
    elif obj_name == "wrapper_api":
        return False
    elif obj_name.startswith("_"):
        return False
    elif not obj:
        return False
    elif isinstance(obj, str):
        return True
    elif isinstance(obj, object):
        return True
    else:
        return False


def obj_to_dict(obj, object_name=None):
    if object_name == "connection_string":
        return connection_string.obfuscate_connection_string(obj)
    elif isinstance(obj, str):
        if "cert" in object_name or "x509" in object_name:
            return "REDACTED"
        else:
            return obj
    elif isinstance(obj, int) or isinstance(obj, bool):
        return obj
    elif isinstance(obj, object):
        dict = {}
        for child_name in dir(obj):
            child = getattr(obj, child_name, None)
            if _can_serialize(child_name, child):
                dict[child_name] = obj_to_dict(child, child_name)
        return dict
    else:
        assert False


def dump_object(obj):
    print(json.dumps(obj_to_dict(obj), indent=2))
