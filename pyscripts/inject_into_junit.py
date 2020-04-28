#l Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
#
# filename: inject_into_junit.py
# author:   v-greach@microsoft.com
# created:  03/11/2019
# Rev: 03/11/2019 D

import sys
import os
import argparse
import shutil
import re
from junitparser import TestCase, TestSuite, JUnitXml


class InjectIntoJunit:
    def __init__(self, args):

        # Parse args
        parser = argparse.ArgumentParser(description="Inject Into Junit")
        parser.add_argument(
            "-junit_file", required=True, nargs=1, help="filename of junit file"
        )
        parser.add_argument(
            "-log_file", required=True, nargs=1, help="filename of log file"
        )
        arguments = parser.parse_args(args)

        junit_file_name = arguments.junit_file[0]
        log_file_nanme = arguments.log_file[0]

        with open(log_file_nanme, "r", encoding="utf8") as f:
            log_file_lines = f.read().splitlines()

        xml = JUnitXml.fromfile(junit_file_name)

        for suite in xml:
            for testcase in suite:
                if testcase:
                    class_name = testcase.classname
                    test_name = testcase.name
                    if testcase.system_out:
                        testcase.system_err = testcase.system_out

                        lines_for_junit = self.get_testcase_lines_from_log(
                            log_file_lines, class_name, test_name
                        )
                        print(
                            "TestCase: "
                            + test_name
                            + " : Injecting ("
                            + str(len(lines_for_junit))
                            + ") lines"
                        )
                        parsed_loglines = "\n".join(lines_for_junit)
                        testcase.system_out = "\n" + parsed_loglines + "\n"

        xml.write()

        # remove offending characters
        with open(junit_file_name, "rt") as f:
            file_content = f.read()
        filtered = self.filter_esc_to_ascii7(file_content)
        with open(junit_file_name, "w") as f:
            f.write(filtered)

        print("SUCCESS!")
        return

    def filter_esc_to_ascii7(self, file_str):
        def is_printable(i):
            o = ord(i)
            return o == 10 or o == 13 or (o < 128 and o >= 32)

        ascii7 = "".join([i if is_printable(i) else "#" for i in file_str])
        ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", str(ascii7))

    def get_testcase_lines_from_log(self, log_lines, class_name, test_name):
        lines_for_junit = []
        # PYTEST: HORTON: Exiting function 'test_iothub_device.TestIotHubDeviceClient' 'test_method_call_invoked_from_service'
        log_start_tag = "Entering function '{}' '{}'".format(class_name, test_name)
        log_end_tag = "Exiting function '{}' '{}'".format(class_name, test_name)

        got_start = False
        for log_line in log_lines:
            if (not got_start) and (log_start_tag in log_line):
                got_start = True
            if got_start:
                lines_for_junit.append(log_line)
                if log_end_tag in log_line:
                    break
        if len(lines_for_junit) == 0:
            lines_for_junit.append(
                "{} ERROR: Did not find any log lines that end with [{}]".format(
                    __file__, log_start_tag
                )
            )
        return lines_for_junit


if __name__ == "__main__":
    junit_processor = InjectIntoJunit(sys.argv[1:])
