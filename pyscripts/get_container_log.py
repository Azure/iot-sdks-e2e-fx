#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#

import sys
import os
import docker
import argparse
from datetime import datetime

class HortonGetContainerLog:
    def __init__(self, args):
        self.get_container_log(args)

    def get_container_log(self, container_name):

        if sys.platform == 'win32':
            base_url = "tcp://127.0.0.1:2375"
        else:
            base_url = "unix://var/run/docker.sock"
            
        api_client = docker.APIClient(base_url=base_url)
        containers = api_client.containers(all=True)
        container = self.get_container_by_name(containers, container_name)
        if not container:
            print("Container {} is not deployed".format(container_name))
            return
        if container['State'] != 'running':
            print("Container {} is not Running".format(container_name))
            return

        log_byte_array = api_client.logs(container, stdout=True, stderr=True, stream=False, timestamps=True,)
        
        log_lines = self.split_byte_array_by_delimiter(log_byte_array, b"\n20")

        for line in log_lines:
            line = self.normalize_timestamp(line)
            line = self.remove_duplicate_timestamp(line)

            log_line_parts = line.split("Z ")
            if len(log_line_parts) > 1 and len(log_line_parts[0]) > 2:
                print(line)

    def remove_duplicate_timestamp(self, log_line):
        log_line_parts = log_line.split("Z ")
        num_parts = len(log_line_parts)

        if num_parts > 1:
            date_parts = log_line_parts[1].split('T')
            if len(date_parts) >= 2:
                time_vals = date_parts[1].split(".")
                if len(time_vals) >= 2:
                    date_parts[1] = time_vals[0] + "." + time_vals[1][:6]
                    time_str = " ".join(date_parts)
                    if self.is_valid_datetime(time_str, "%Y-%m-%d %H:%M:%S.%f"):
                        log_line_parts.remove(log_line_parts[1]) 
                        log_line = "Z ".join(log_line_parts)
        return log_line

    def normalize_timestamp(self, log_line):
        log_line_parts = log_line.split("Z ")
        num_parts = len(log_line_parts)

        if num_parts > 1:
            date_parts = log_line_parts[0].split('T')
            if date_parts:
                time_vals = date_parts[1].split(".")
                if time_vals:
                    date_parts[1] = time_vals[0] + "." + time_vals[1][:6]
                    time_str = " ".join(date_parts)
                    time_str = self.convert_datetime(time_str, "%y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f")
                    log_line_parts[0] = time_str                           
                    log_line = "Z ".join(log_line_parts)
        return log_line

    def split_byte_array_by_delimiter(self, byte_array, log_delimiter):
        byte_array_len = len(byte_array)
        byte_pos = -1
        byte_last_pos = 0
        log_delimiter_len = len(log_delimiter)
        log_lines = []
        for _ in range(0, byte_array_len):
            delimeter_match = False
            byte_pos += 1
            if byte_pos + log_delimiter_len < byte_array_len:
                for i in range(0, log_delimiter_len):
                    if byte_array[i + byte_pos] != log_delimiter[i]:
                        break
                    if i == log_delimiter_len - 1:
                        delimeter_match = True
            if delimeter_match:
                bin_buffer = ""
                for b in range(byte_last_pos, byte_pos):
                    if byte_array[b] >= 128:
                        bin_buffer += "#"
                    else:
                        bin_buffer += chr(byte_array[b])
                byte_last_pos = byte_pos + log_delimiter_len
                byte_pos = byte_last_pos
                log_lines.append(bin_buffer)
                delimeter_match = False

        if byte_last_pos < byte_array_len:
            bin_buffer = ""
            for b in range(byte_last_pos, byte_array_len):
                if byte_array[b] >= 128:
                    bin_buffer += "#"
                else:
                    bin_buffer += chr(byte_array[b])
            log_lines.append(bin_buffer)

        return log_lines

    def is_valid_datetime(self, date_str, date_format):
        try:
            ts_fmt = datetime.strptime(date_str , date_format)
            cvt_ds = ts_fmt.strftime(date_format)
            time_vals = cvt_ds.split(".")
            if len(time_vals) >= 2:
                if len(time_vals[1]) > 3:
                    time_vals[1] = time_vals[1][:3]
                cvt_ds = time_vals[0] + "." + time_vals[1]

            if date_str != cvt_ds:
                raise ValueError
            return True
        except ValueError:
            return False

    def convert_datetime(self, date_str, date_format, date_format_out):
        try:
            ts_fmt = datetime.strptime(date_str , date_format)
            cvt_ds = ts_fmt.strftime(date_format_out)
            return cvt_ds
        except ValueError:
            return ""

    def get_container_by_name(self, containers, container_name):
        container = None
        for container in containers:
            ctr_names = container.get('Names')
            for ctr_name in ctr_names:
                ctr_name = ctr_name.strip('/')
                if container_name == ctr_name:
                    return container
        return container

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get docker log for container')
    parser.add_argument('--container', required=True, help='path and filename of manifest', type=str)
    arguments = parser.parse_args()
    horton_containers = HortonGetContainerLog(arguments.container)
