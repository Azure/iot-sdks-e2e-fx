# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import threading


class ExcThread(threading.Thread):
    def __init__(self, target, args=None):
        self.args = args if args else []
        self.target = target
        self.exc = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.target(*self.args)
        except Exception as e:
            # self.exc =sys.exc_info()
            self.exc = e
