# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


memory_stats_to_collect = ["MemTotal", "MemFree", "MemAvailable"]
process_stats_to_collect = [
    "VmSize",
    "VmRSS",
    "RssFile",
    "RssShmem",
    "voluntary_ctxt_switches",
    "nonvoluntary_ctxt_switches",
]


def get_stats(filename, prefix, stats_to_collect):
    """
    collect status from a /prox/* file
    """
    stats = {}
    with open(filename) as stream:
        lines = stream.readlines()
    for line in lines:
        words = line.split()
        key = words[0].rstrip(":")
        value = words[1]
        if key in stats_to_collect:
            stats[prefix + key] = value
    return stats


def get_memory_stats():
    """
    collect stats on system memory use
    """
    return get_stats("/proc/meminfo", "system_", memory_stats_to_collect)


def get_system_uptime():
    """
    return system uptime in seconds
    """
    with open("/proc/uptime") as stream:
        line = stream.readline()
    return float(line.split()[0])


def get_process_stats(pid):
    """
    collect stats for process behavior
    """
    return get_stats(
        "/proc/{}/status".format(pid), "process_", process_stats_to_collect
    )
