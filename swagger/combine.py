# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import argparse
import json
import copy

parser = argparse.ArgumentParser(prog="combine_swagger")

parser.add_argument("--output", "-o", help="named of output file", type=str)
parser.add_argument(
    "input_file", type=str, help="input file", action="append", nargs="+"
)
args = parser.parse_args()

output_dict = {"tags": [], "paths": {}}

for name in args.input_file[0]:
    print("Reading " + name)
    with open(name) as json_file:
        input_dict = json.load(json_file)

    for tag in input_dict["tags"]:
        output_dict["tags"].append(tag)
    for path in input_dict["paths"]:
        output_dict["paths"][path] = input_dict["paths"][path]

    for key in input_dict:
        if key not in ["tags", "paths"]:
            output_dict[key] = input_dict[key]

print("Writing " + args.output)
with open(args.output, "w") as json_file:
    json.dump(output_dict, json_file, indent=4)
