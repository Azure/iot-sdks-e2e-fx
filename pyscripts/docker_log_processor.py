#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: docker_log_processor.py
# author:   v-greach@microsoft.com
# created:  01/29/2019

from multiprocessing import Process, Queue, Event
from threading import Thread
from datetime import datetime, timedelta
import docker
import time
import argparse
import sys

class DockerLogProcessor:

    def __init__(self, container_names, options=""):

        run_static = False
        if options:
            if "-staticfile" in options:
                run_static = True
                self.process_static_log(options)

        if run_static == False:
            self.queue = Queue()

            self.logger_thread = Thread(target = self.process_queue)
            self.logger_thread.start()

            self.watcher_processes = []

            for container_name in container_names:
                print("Getting Log for: " + container_name)
                new_process =  Process(target = DockerLogProcessor.get_log_from_container, args=(container_name, self.queue, options))
                new_process.start()
                self.watcher_processes.append(new_process)

    @classmethod
    def format_date_and_time(self, date_in="", time_format="%Y-%m-%d %H:%M:%S.%f"):
        """
        Formats a sting into a datetime type.

        string comes in, if it's empty, set it to NOW,
        then using the format, convert the string to datetime type.

        Parameters
        ----------
        date_in : string
            String to convert - call be null
        time_format : string
            format of string for datetime conversion

        Returns
        -------
        datetime
            converted input string or NOW() if empty
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
    def get_log_from_container(container_name, queue, options):
        """
        Gets log info from the Docker container.

        Parameters
        ----------
        container_name : string
            Name of the Docker container
        queue : object
            queue to stuff the log object in
        options : string
            Options - basically the argv passed to the class
        """
        client = docker.from_env()
        container = client.containers.get(container_name)

        for log_line in container.logs(stream=True, tail=0, follow=True, timestamps=True):
            try:
                log_line = log_line.decode('utf8').strip()
                log_line_parts = log_line.split("Z ")
                log_line_object = LogLineObject(DockerLogProcessor.format_date_and_time(log_line_parts[0]), container_name, log_line_parts[1])
                queue.put(log_line_object)
            except Exception as e:
                write_err("Exception getting container log_line from: " + container_name)
                self.write_err(e)

    def split(self, string, delimiters):
        """
        Split a string with multiple delimiters.
        """
        import re
        regexPattern = '|'.join(map(re.escape, delimiters))
        return re.split(regexPattern, string)

    def write_err(self, msg):
        """
        write a string to stdout and stderr.
        """         
        print(msg, file=sys.stderr)
        print(msg)

    def get_timestamp_delta(self, date_one, date_two, line_count = 0, line_mod = 100):
        """
        Diff date_one and date_two then format string for readability.

        Delta of the strings are slammed into submission by fields.
        line_count can be used to print a full timestamp every line_mod lines

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

    def process_static_log(self, options):
        """
        Got some static logs - set 'em up for processing.

        Static log(s) specified.
        parse the options with argparse.
            get a list of string of filenames to proceas,
            get the output filename,
            get json filters.
        read all log files and format each line
        sort and push to output
        """
        write_log_filename = "logsbytime.log"
        split_str = ' ' + u"\u2588" + ' '

        loglines = []
        max_name_len = 0
        filter_json_file = ""
        filter_list = ""
        pytest_owner = ""

        parser = argparse.ArgumentParser(description="Docker Log Processor")
        parser.add_argument('-outputfile', nargs=1, help="filename to write output")
        parser.add_argument('-staticfile', nargs='+', help="filename to read from")
        parser.add_argument('-filterfile', nargs=1, help="filename of json filters")
        arguments = parser.parse_args(options.split(' '))

        import os
        dir_name = os.path.dirname(os.path.abspath(__file__))
        out_filenames = arguments.outputfile
        if len(out_filenames) > 1:
            self.write_err("ERR: Too many -outfiles")
            return
        else:
            out_filename = out_filenames[0]
            out_filename = out_filename.strip()
            write_log_filename = os.path.basename(out_filename)

        import json
        filter_filenames = arguments.filterfile
        if len(filter_filenames) > 1:
            self.write_err("ERR: Too many -filterfile")
            return
        else:
            filter_filename = filter_filenames[0]
            filter_json_file = filter_filename.strip()
            full_filter_path = os.path.join(os.sep, dir_name, filter_json_file)
            try:
                filter_json = open(full_filter_path, encoding="utf8").read()
                if filter_json:
                    json_data  = json.loads(filter_json)
                    filter_list = json_data['filters']
            except Exception as e:
                self.write_err("Exception processing JSON file: " + full_filter_path)
                self.write_err(e)
                return

        static_filenames = arguments.staticfile
        # find the max_name_len of every staticfile filename
        for static_filename in static_filenames:
            if static_filename:
                static_filename = static_filename.strip()
                base_filename = os.path.basename(static_filename)
                name_len = len(base_filename)
                if name_len > max_name_len:
                    max_name_len = name_len

        for static_filename in static_filenames:
            if static_filename:
                static_filename = static_filename.strip()
                base_filename = os.path.basename(static_filename)

                module_name = base_filename
                # Pad the filename so that each is the same length
                for _ in range(len(base_filename), max_name_len):
                    module_name += ' '

                full_log_path = os.path.join(os.sep, dir_name, static_filename)
                try:
                    read_file = open(full_log_path, encoding="utf8").read().split("\n")
                except Exception as e:
                    self.write_err("Exception opening LOG file: " + full_log_path )
                    self.write_err(e)
                
                # Get and filter each line
                for log_line in read_file:
                    ok_to_log = True
                    if log_line:
                        if "PYTEST" in log_line:
                            if not pytest_owner:
                                pytest_owner = base_filename
                            else:
                                if pytest_owner != base_filename:
                                    ok_to_log = False

                        if ok_to_log:
                            for filter in filter_list:
                                if filter in log_line:
                                    ok_to_log = False

                        if ok_to_log:
                            # Made it past filters and BuinessLogic, LOG IT
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

                                log_time = DockerLogProcessor.format_date_and_time(log_line_parts[0], "%Y-%m-%d %H:%M:%S.%f")
                                log_line_object = LogLineObject(log_time, module_name, log_data)
                                loglines.append(log_line_object)

        loglines.sort(key=lambda x: x.timestamp)
        last_timestamp = datetime.now() + timedelta(days=-364)
        line_count = 0

        #Done processing  and sorted, now display and write results
        write_log_filename = os.path.join(os.sep, dir_name, write_log_filename)
        with open(write_log_filename,'w', encoding="utf-8") as outfile: 
            for log_line in loglines:
                logline_timestamp = log_line.timestamp
                date_delta = self.get_timestamp_delta(str(logline_timestamp), str(last_timestamp), line_count)
                line_count += 1
                out_line = log_line.module_name + " : " + date_delta + split_str +  log_line.log_data
                #print(out_line)
                print(out_line[0:125])
                outfile.write("{}\n".format(out_line))
                last_timestamp = logline_timestamp

    def process_queue(self):
        """
        Process the line objects in the queue, and print as formatted.
        """        
        last_timestamp = datetime.now() + timedelta(days=-364)
        line_count = 0
        while True:
            log_line = self.queue.get()

            logline_timestamp = log_line.timestamp
            date_delta = self.get_timestamp_delta(str(logline_timestamp), str(last_timestamp), line_count)
            line_count += 1
            print(log_line.module_name + " : " + date_delta + " : " +  log_line.log_data)
            last_timestamp = logline_timestamp

class LogLineObject:  
    def __init__ (self, timestamp, module_name='', log_data=''):  
        self.timestamp    = timestamp
        self.module_name  = module_name  
        self.log_data     = log_data  
if __name__ == "__main__":
    log_processor = DockerLogProcessor([], " ".join(sys.argv[1:]))
