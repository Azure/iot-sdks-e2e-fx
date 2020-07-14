# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
from dictionary_object import DictionaryObject


class WrapperProperties(DictionaryObject):
    def __init__(self):
        super(WrapperProperties, self).__init__()

        self.sdk_repo = ""
        self.sdk_branch = ""
        self.sdk_uri = ""

        self.wrapper_gc_object_count = 0
        self.wrapper_pid

        self.lock_attributes()


class SystemProperties(DictionaryObject):
    def __init__(self):
        super(SystemProperties, self).__init__()

        self.system_memory_total = 0
        self.system_memory_used = 0
        self.system_memory_free = 0
        self.system_uptime = 0

        self.wrapper_virtual_memory
        self.wrapper_physical_memory
        self.wrapper_shared_memory
        self.wrapper_cpu_percent
        self.wrapper_memory_percent
        self.wrapper_cpu_time

        self.lock_attributes()
