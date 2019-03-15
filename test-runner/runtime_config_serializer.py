# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import connection_string
import runtime_config_templates


def _can_serialize(obj_name, obj):
    if obj_name.startswith("__"):
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
    if obj is runtime_config_templates.SET_AT_RUNTIME:
        return obj
    elif object_name is "connection_string":
        return connection_string.obfuscate_connection_string(obj)
    elif object_name in ["ca_certificate", "certificate"]:
        return "REDACTED"
    elif isinstance(obj, str):
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
