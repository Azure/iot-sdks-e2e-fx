# Copyright (c) Microsoft. All rights reserved.
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

        junit_path = arguments.junit_file[0]
        merge_log_path = arguments.log_file[0]
        junit_base_path = junit_path.lower().split(".xml")
        junit_save_path = junit_base_path[0] + "_MERGED.xml"

        try:
            shutil.copyfile(junit_path, junit_save_path)
        except Exception as e:
            print("Exception copying JUNIT file: " + junit_path)
            print(e)
            return

        try:
            with open(merge_log_path, "r", encoding="utf8") as f:
                read_file = f.read().splitlines()

        except Exception as e:
            print("Exception opening LOG file: " + merge_log_path)
            print(e)
            return

        from junitparser import TestCase, TestSuite, JUnitXml

        try:
            xml = JUnitXml.fromfile(junit_save_path)
        except Exception as e:
            print("Exception opening JUNIT file: " + junit_save_path)
            print(e)
            return

        for testcase in xml:
            if testcase:
                class_name = testcase.classname
                test_name = testcase.name
                if testcase.system_out:
                    lines_for_junit = self.get_testcase_lines_from_log(
                        read_file, class_name, test_name
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
        try:
            xml.write()
        except Exception as e:
            print("Exception writing JUNIT file: " + junit_save_path)
            print(e)
            return

        # remove offending characters
        with open(junit_save_path, "rt") as f:
            file_content = f.read()
        filtered = self.filter_esc_to_ascii7(file_content)
        with open(junit_save_path, "w") as f:
            f.write(filtered)

        try:
            shutil.copyfile(junit_save_path, junit_path)
        except Exception as e:
            print("Exception copying JUNIT file: " + junit_path)
            print(e)

        print("SUCCESS!")
        return

    def filter_esc_to_ascii7(self, file_str):
        ascii7 = "".join([i if ord(i) < 128 else "#" for i in file_str])
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
