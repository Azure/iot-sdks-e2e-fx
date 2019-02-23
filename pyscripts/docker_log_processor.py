#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# docker_log_processor.py
# v-greach@microsoft.com

from multiprocessing import Process, Queue, Event
from threading import Thread
from datetime import datetime, timedelta
import docker
import time
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
        client = docker.from_env()
        container = client.containers.get(container_name)

        for log_line in container.logs(stream=True, tail=0, follow=True, timestamps=True):
            try:
                log_line = log_line.decode('utf8').strip()
                log_line_parts = log_line.split("Z ")
                log_line_object = LogLineObject(DockerLogProcessor.format_date_and_time(log_line_parts[0]), container_name, log_line_parts[1])
                queue.put(log_line_object)
            except Exception as e:
                print(e)

    def split(self, string, delimiters):
        import re
        regexPattern = '|'.join(map(re.escape, delimiters))
        return re.split(regexPattern, string)

    def get_timestamp_delta(self, date_one, date_two, line_count):
        show_full_timestamp_every_num_lines = 100
        if line_count % show_full_timestamp_every_num_lines == 0:
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
        
        split_str = ' ' + u"\u2588" + ' '

        loglines = []
        max_name_len=0
        import os

        opt_list = options.split("-staticfile")

        for static_filename in opt_list:
            if static_filename:
                static_filename = static_filename.strip()
                base_filename = os.path.basename(static_filename)
                name_len = len(base_filename)
                if name_len > max_name_len:
                    max_name_len = name_len

        for static_filename in opt_list:
            if static_filename:
                static_filename = static_filename.strip()
                base_filename = os.path.basename(static_filename)

                module_name = base_filename
                for _ in range(len(base_filename), max_name_len):
                    module_name += ' '

                read_file = open(static_filename, encoding="utf8").read().split("\n")

                for log_line in read_file:
                    if log_line:
                        log_line_parts = log_line.split("Z ")
                        if log_line_parts:
                            log_time = DockerLogProcessor.format_date_and_time(log_line_parts[0], "%Y-%m-%d %H:%M:%S.%f")
                            log_line_object = LogLineObject(log_time, module_name, log_line_parts[1])
                            loglines.append(log_line_object)

        loglines.sort(key=lambda x: x.timestamp)

        last_timestamp = datetime.now() + timedelta(days=-364)
        line_count = 0

        for log_line in loglines:
            logline_timestamp = log_line.timestamp
            date_delta = self.get_timestamp_delta(str(logline_timestamp), str(last_timestamp), line_count)
            line_count += 1
            out_line = log_line.module_name + " : " + date_delta + split_str +  log_line.log_data
            print(out_line)
            
            last_timestamp = logline_timestamp

    def process_queue(self):
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
        self.timestamp = timestamp
        self.module_name  = module_name  
        self.log_data  = log_data  

if __name__ == "__main__":
    log_processor = DockerLogProcessor([], " ".join(sys.argv[1:]))
