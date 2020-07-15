# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


def get_memory_stats():
    """
    return total memory, free memory, and available memory
    """
    mem_total = 0
    mem_free = 0
    mem_available = 0
    with open("/proc/meminfo") as stream:
        lines = stream.readlines()
    for line in lines:
        words = line.split()
        if words[0].startswith("MemTotal"):
            mem_total = int(words[1]) * 1024
        elif words[0].startswith("MemFree"):
            mem_free = int(words[1]) * 1024
        elif words[0].startswith("MemAvailable"):
            mem_available = int(words[1]) * 1024
    return mem_total, mem_free, mem_available


def get_system_uptime():
    """
    return system uptime in seconds
    """
    with open("/proc/uptime") as stream:
        line = stream.readline()
    return float(line.split()[0])
