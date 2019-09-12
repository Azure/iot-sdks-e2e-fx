# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
import adapters
import runtime_config
from msrest.exceptions import HttpOperationError

hardcoded_skip_list = {
    "node": [],
    "csharp": ["module_under_test_has_device_wrapper", "handlesLoopbackMessages"],
    "python": [
        "module_under_test_has_device_wrapper",
        "invokesModuleMethodCalls",
        "invokesDeviceMethodCalls",
    ],
    "pythonpreview": [
        "receivesMethodCalls",
        "invokesModuleMethodCalls",
        "invokesDeviceMethodCalls",
        "supportsTwin",
        "handlesLoopbackMessages",
    ],
    "c": ["module_under_test_has_device_wrapper"],
    "java": ["module_under_test_has_device_wrapper", "supportsTwin"],
}

capabilities = None
got_caps = False


def get_skip_list(language):
    if language == "ppdirect":
        language = "pythonpreview"
    caps = get_test_module_capabilities()
    if caps and "skip_list" in caps:
        return caps["skip_list"]
    else:
        return hardcoded_skip_list[language]


default_flags = {
    "supports_async": False,
    "new_message_format": False,
    "security_messages": False,
}


def get_test_module_capabilities_flag(flag_name):
    caps = get_test_module_capabilities()
    if caps and "flags" in caps and flag_name in caps["flags"]:
        return caps["flags"][flag_name]
    else:
        return default_flags[flag_name]


def get_all_capabilities_flags():
    return default_flags.keys()


def get_test_module_capabilities():
    global capabilities
    global got_caps

    if got_caps:
        return capabilities
    else:
        test_wrapper = runtime_config.get_test_module_wrapper_api()
        if test_wrapper:
            try:
                capabilities = test_wrapper.get_capabilities()
            except HttpOperationError:
                capabilities = None
        got_caps = True
        return capabilities


def set_test_module_flag(flag_name, flag_value):
    test_wrapper = runtime_config.get_test_module_wrapper_api()
    test_wrapper.set_flags({flag_name: flag_value})
