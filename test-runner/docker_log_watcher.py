#!/usr/bin/env python
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from multiprocessing import Process, Queue, Event
from threading import Thread
import uuid
import docker

try:
    # on Windows, we get a different exception from docker when it can't connect to the daemon :(
    import pywintypes
    no_container_exception = pywintypes.error
except:
    no_container_exception = docker.errors.NotFound


class DockerLogWatcher:
    def __init__(self, container_names, filters):
        self.queue = Queue()

        self.silent = True
        self.kill_marker = uuid.uuid4()
        self.flush_marker = uuid.uuid4()
        self.flush_complete = Event()

        self.logger_thread = Thread(target = self.queue_reader)
        self.logger_thread.start()

        self.watcher_processes = []
        for container_name in container_names:
            print("watching " + container_name)
            new_process =  Process(target = DockerLogWatcher.log_reader_subprocess, args=(self.queue, container_name, filters))
            new_process.start()
            self.watcher_processes.append(new_process)

    def terminate(self):
        for subprocess in self.watcher_processes:
            subprocess.terminate()
        self.queue.put(self.kill_marker)

    def enable(self):
        self.silent = False

    def flush_and_disable(self):
        self.flush_complete.clear()
        self.queue.put(self.flush_marker)
        self.flush_complete.wait()

    def queue_reader(self):
        while True:
            line = self.queue.get()
            if line == self.kill_marker:
                return
            elif line == self.flush_marker:
                self.silent = True
                self.flush_complete.set()
            elif not self.silent:
                print(line)

    @staticmethod
    def log_reader_subprocess(queue, container_name, filters):
        client = docker.from_env()
        try:
            container = client.containers.get(container_name)
            for line in container.logs(stream=True, tail=0, follow=True):
                line = line.decode("ascii")
                if not any(filter in line for filter in filters):
                    queue.put("{}: {}".format(container.name, line.strip()))
        except no_container_exception:
            pass

