#!/usr/bin/env python
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

class InjectIntoJunit:

    def __init__(self, args):

        # Parse args
        parser = argparse.ArgumentParser(description="Inject Into Junit")
        parser.add_argument('-junit_file', required=True, nargs=1, help="filename of junit file")
        parser.add_argument('-log_file', required=True, nargs=1, help="filename of log file")
        arguments = parser.parse_args(args)

        junit_path = arguments.junit_file[0]
        merge_log_path = arguments.log_file[0]
        junit_base_path = junit_path.lower().split(".xml")
        junit_save_path = junit_base_path[0] + "_MERGED.xml"

        try:
            shutil.copyfile(junit_path, junit_save_path)
        except Exception as e:
            print("Exception copying JUNIT file: " + junit_path )
            print(e)
            return

        try:
            with open(merge_log_path, 'r', encoding="utf8") as f:
                read_file = f.read().splitlines()

        except Exception as e:
            print("Exception opening LOG file: " + merge_log_path )
            print(e)
            return

        from junitparser import TestCase, TestSuite, JUnitXml
        try:
            xml = JUnitXml.fromfile(junit_save_path)
        except Exception as e:
            print("Exception opening JUNIT file: " + junit_save_path )
            print(e)
            return

        for suite in xml:
            if(suite):
                suite_name = suite.name
                if(suite.system_out):
                    lines_for_junit = self.get_suite_lines_from_log(read_file, suite_name)
                    print("TestSuite: " + suite_name + " : Injecting (" + str(len(lines_for_junit)) + ") lines")
                    parsed_loglines  = '\n'.join(lines_for_junit)
                    suite.system_out = '\n' + parsed_loglines + '\n'
        try:
            xml.write()
        except Exception as e:
            print("Exception writing JUNIT file: " + junit_save_path )
            print(e)
            return

        try:
            shutil.copyfile(junit_save_path, junit_path)
        except Exception as e:
            print("Exception copying JUNIT file: " + junit_path )
            print(e)

        print("SUCCESS!")
        return

    def get_suite_lines_from_log(self, log_lines, suite_name):
        lines_for_junit = []
        log_start_tag = "PYTEST: HORTON: Entering function " + suite_name
        log_end_tag = "PYTEST: HORTON: Exiting function " + suite_name

        got_start = False
        for log_line in log_lines:
            if(got_start == False and log_start_tag in log_line):
                got_start = True
            if(got_start):
                lines_for_junit.append(log_line)
                if(log_end_tag in log_line):
                    break
        return lines_for_junit

if __name__ == "__main__":
    junit_processor = InjectIntoJunit(sys.argv[1:])
