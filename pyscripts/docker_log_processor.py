#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: docker_log_processor.py
# author:   v-greach@microsoft.com
# created:  01/29/2019
# Rev: 03/05/2019 A

from multiprocessing import Process, Queue, Event
from threading import Thread
from datetime import datetime, timedelta
import docker
import time
import argparse
import sys

class DockerLogProcessor:

    def __init__(self, args):

        # Parse args
        parser = argparse.ArgumentParser(description="Docker Log Processor")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-staticfile', action='append', nargs='+', help="filename to read from")
        group.add_argument('-modulename', action='append', nargs='+', help="docker modulename to read from")
        parser.add_argument('-filterfile', nargs=1, help="filename of json filters")
        arguments = parser.parse_args(args)

        if arguments.staticfile:
            self.process_static_log(arguments.staticfile, arguments.filterfile)
        else:
            self.queue = Queue()
            self.logger_thread = Thread(target = self.process_queue)
            self.logger_thread.start()
            self.watcher_processes = []

            for container_name in arguments.modulename:
                print("Getting Log for: " + container_name)
                new_process =  Process(target = self.get_log_from_container, args=(container_name, self.queue))
                new_process.start()
                self.watcher_processes.append(new_process)

    @classmethod
    def format_date_and_time(self, date_in="", time_format="%Y-%m-%d %H:%M:%S.%f"):
        """
        Formats a string into a datetime type.

        date_in comes in, if it's empty, set it to NOW,
        then using the format, convert the string to datetime type.

        Parameters
        ----------
        date_in : string
            String to convert - can be null
        time_format : string
            format of string for datetime conversion

        Returns
        -------
        datetime
            converted input string or NOW() if date_in is empty
        """
        date_out =""
        if not date_in:
            date_out = datetime.strftime(datetime.now(), time_format)
            return date_out
        date_in = date_in.replace('T', ' ')
        if len(date_in) > 26:
            date_in = date_in[:26]
        date_out = datetime.strptime(date_in, time_format)
        return date_out

    @staticmethod
    def write_err(msg):
        """
        write a string to stdout and stderr.
        """         
        print(msg, file=sys.stderr)
        print(msg)

    @staticmethod
    def get_log_from_container(container_name, queue):
        """
        Gets log info from the Docker container then converts DateTime
            and puts each line in the queue.

        Parameters
        ----------
        container_name : string
            Name of the Docker container
        queue : object
            queue to stuff the log object in
        """
        client = docker.from_env()
        container = client.containers.get(container_name)

        for log_line in container.logs(stream=True, tail=0, follow=True, timestamps=True):
            try:
                log_line = log_line.decode('utf8').strip()
                log_line_parts = log_line.split("Z ")

                if log_line_parts:
                    log_data = ""
                    num_parts = len(log_line_parts)

                    # Handle case where more than one timestamp
                    if num_parts > 2:
                        for part in range(1, num_parts):    
                            log_data += log_line_parts[part] + ' '
                    else:
                        log_data = log_line_parts[1]

                log_line_object = LogLineObject(DockerLogProcessor.format_date_and_time(log_line_parts[0]), container_name, log_data)
                queue.put(log_line_object)
            except Exception as e:
                DockerLogProcessor.write_err("Exception getting container log_line from: " + container_name)
                DockerLogProcessor.write_err(e)

    def split(self, string, delimiters):
        """
        Split a string with multiple delimiters.
        """
        import re
        regexPattern = '|'.join(map(re.escape, delimiters))
        return re.split(regexPattern, string)

    def get_timestamp_delta(self, date_one, date_two, line_count = 0, line_mod = 100):
        """
        Diff date_one and date_two then format string for readability.

        Delta of the strings are converted by fields.
        line_count can be used to print a full timestamp every line_mod (%) lines

        """
        if line_mod != 0 and line_count % line_mod == 0:
            return date_one

        time_delta_str = ""
        delimiters  = ('.', '-', ' ', ':')
        field_count = 0

        all_fields_one = self.split(date_one, delimiters)
        all_fields_two = self.split(date_two, delimiters)
        for field1 in all_fields_one:
            if field1 == all_fields_two[field_count]:
                for _ in field1:
                    time_delta_str += " "
            else:
                time_delta_str += all_fields_one[field_count]
            if field_count < 2:
                time_delta_str += "-"
            elif field_count == 2:
                time_delta_str += " "
            elif field_count > 2 and field_count < 5 :
                time_delta_str += ":"
            elif field_count == 5 :
                time_delta_str += "."    
            field_count += 1
        return time_delta_str

    def process_static_log(self, static_filenames, filter_filenames):
        """
        Static logs in args - set them up for processing.

        Static log(s) specified.
            static_filenames
        Optional filter_filename
            Path to JSON filter file

        read all log files and format each line
        sort and display to stdout
        """
        import os
        import json
        import pathlib

        split_char = u"\u2588"
        loglines = []
        max_name_len = 0
        filter_list = ""
        pytest_owner = ""
        
        if filter_filenames:
            filter_filename = os.path.abspath(filter_filenames[0])
            """
            filter.json should have a format like this:
                {
                    "filters":
                    [
                        "Getting next batch",
                        "Obtained next batch"
                    ]
                }
            """
            try:
                filter_json = open(filter_filename, encoding="utf8").read()
                if filter_json:
                    json_data  = json.loads(filter_json)
                    filter_list = json_data['filters']
            except Exception as e:
                self.write_err("Exception processing JSON file: " + filter_filename)
                self.write_err(e)

        # find the max_name_len of every staticfile filename basename
        for static_filename in static_filenames:
            if static_filename:
                base_filename = os.path.basename(static_filename[0])
                name_len = len(base_filename)
                if name_len > max_name_len:
                    max_name_len = name_len

        # read and process every static file
        for static_filename in static_filenames:
            if static_filename:
                static_filename = static_filename[0]
                module_name = os.path.basename(static_filename)
                print("Getting log from file: " + static_filename)
                # Pad the filename so that each is the same length
                for _ in range(len(module_name), max_name_len):
                    module_name += ' '
                try:
                    read_file = open(static_filename, encoding="utf8").read().split("\n")
                except Exception as e:
                    self.write_err("Exception opening LOG file: " + static_filename )
                    self.write_err(e)
                    return
               
                # Get and filter each line
                for log_line in read_file:
                    ok_to_log = True
                    if log_line:
                        if "PYTEST" in log_line:
                            if not pytest_owner:
                                pytest_owner = module_name
                            else:
                                if pytest_owner != module_name:
                                    ok_to_log = False
                        if ok_to_log:
                            for filter in filter_list:
                                if filter in log_line:
                                    ok_to_log = False

                        if ok_to_log:
                            # Made it past filters and PyTest, so Log the line
                            log_line_parts = log_line.split("Z ")
                            if log_line_parts:
                                valid_line = False
                                log_data = ""
                                num_parts = len(log_line_parts)

                                # Handle case where more than one timestamp
                                if num_parts > 2:
                                    for part in range(1, num_parts):    
                                        log_data += log_line_parts[part] + ' '
                                else:
                                    if num_parts == 2:
                                        log_data = log_line_parts[1]
                                if num_parts >= 2:
                                    try:
                                        log_time = DockerLogProcessor.format_date_and_time(log_line_parts[0], "%Y-%m-%d %H:%M:%S.%f")
                                        valid_line = True
                                    except:
                                        print("INVALID_TIMESTAMP({}):{}".format(module_name, log_line))
                                    if valid_line:
                                        log_line_object = LogLineObject(log_time, module_name, log_data)
                                        loglines.append(log_line_object)
                                else:
                                    print("INVALID_LINE({}):{}".format(module_name, log_line))

        # Sort the merged static file lines by timestamp
        loglines.sort(key=lambda x: x.timestamp)
        last_timestamp = datetime.now() + timedelta(days=-364)
        line_count = 0

        # display the results to stdout
        for log_line in loglines:
            logline_timestamp = log_line.timestamp
            if  "HORTON: Entering function" in log_line.log_data or "HORTON: Exiting function" in log_line.log_data:
                date_delta = str(logline_timestamp)
            else:
                date_delta = self.get_timestamp_delta(str(logline_timestamp), str(last_timestamp), line_count)
            line_count += 1
            out_line = log_line.module_name + " : " + date_delta + " " + split_char + " " +  log_line.log_data
            last_timestamp = logline_timestamp
            try:
                print(out_line)
            except Exception:
                print(''.join([i if ord(i) < 128 else '#' for i in out_line]))

    def process_queue(self):
        """
        Process the line objects in the queue, and print as formatted.
        """        
        last_timestamp = datetime.now() + timedelta(days=-364)
        line_count = 0
        split_char = u"\u2588"
        while True:
            log_line = self.queue.get()
            logline_timestamp = log_line.timestamp
            if  "HORTON: Entering function" in log_line.log_data or "HORTON: Exiting function" in log_line.log_data:
                date_delta = str(logline_timestamp)
            else:
                date_delta = self.get_timestamp_delta(str(logline_timestamp), str(last_timestamp), line_count)
            line_count += 1
            last_timestamp = logline_timestamp
            out_line = log_line.module_name + " : " + date_delta + " " + split_char +  " " + log_line.log_data
            try:
                print(out_line)
            except Exception:
                print(''.join([i if ord(i) < 128 else '#' for i in out_line]))

class LogLineObject:  
    def __init__ (self, timestamp, module_name='', log_data=''):  
        self.timestamp    = timestamp
        self.module_name  = module_name  
        self.log_data     = log_data  

if __name__ == "__main__":
    log_processor = DockerLogProcessor(sys.argv[1:])
    