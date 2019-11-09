# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import argparse
import deploy
import utilities

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="deploy iothub instance for testing")
    parser.add_argument(
        "--image", help="docker image to deploy", type=str, required=True
    )
    args = parser.parse_args()
    utilities.get_language_from_image_name(args.image)
    deploy.deploy_for_iothub(args.image)
