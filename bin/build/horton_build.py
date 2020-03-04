# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import json
import sys
from . import docker_tags
import argparse
import datetime
import colorama
from colorama import Fore
import subprocess

colorama.init(autoreset=True)

default_repo = "(Azure/azure-iot-sdk-BLAH)"
all_languages = ["c", "csharp", "pythonv2", "node", "java"]

print_separator = "".join("/\\" for _ in range(80))

if sys.platform == "win32":
    base_url = "tcp://127.0.0.1:2375"
else:
    base_url = "unix://var/run/docker.sock"


def get_dockerfile_directory(tags):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.normpath(
        os.path.join(script_dir, "../../docker_images/" + tags.language)
    )


class DockerSubprocessException(Exception):
    pass


def run_docker_command(cmdline):
    print(Fore.YELLOW + "running [{}]".format(cmdline))
    with subprocess.Popen(
        cmdline,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
    ) as proc:
        while proc.poll() is None:
            line = proc.stdout.readline().strip()
            if line:
                print(line)
        if proc.returncode:
            raise DockerSubprocessException(
                "docker returned {}".format(proc.returncode)
            )


def build_image(tags):
    print(print_separator)
    print("BUILDING IMAGE")
    print(print_separator)

    build_args = {
        "HORTON_REPO": tags.repo,
        "HORTON_COMMIT_NAME": tags.commit_name,
        "HORTON_COMMIT_SHA": tags.commit_sha,
    }
    build_arg_string = ""
    for arg in build_args:
        build_arg_string += "--build-arg {}={} ".format(arg, build_args[arg])

    if tags.image_tag_to_use_for_cache:
        cache_from_string = "--cache-from {}:{}".format(
            tags.docker_full_image_name, tags.image_tag_to_use_for_cache
        )
    else:
        cache_from_string = ""

    if tags.variant:
        dockerfile = "Dockerfile." + tags.variant
    else:
        dockerfile = "Dockerfile"

    run_docker_command(
        "docker build --tag {tag} --file {path}/{dockerfile} {build_arg_string} {cache_from_string} {path}".format(
            tag=tags.docker_image_name,
            dockerfile=dockerfile,
            build_arg_string=build_arg_string,
            cache_from_string=cache_from_string,
            path=get_dockerfile_directory(tags),
        )
    )


def tag_images(tags):
    print(print_separator)
    print("TAGGING IMAGE")
    print(print_separator)

    print("Adding tags")
    for image_tag in tags.image_tags:
        print("Adding " + image_tag)
        run_docker_command(
            "docker tag {} {}:{}".format(
                tags.docker_image_name, tags.docker_full_image_name, image_tag
            )
        )


def push_images(tags):
    print(print_separator)
    print("PUSHING IMAGE")
    print(print_separator)

    for image_tag in tags.image_tags:
        print("Pushing {}:{}".format(tags.docker_full_image_name, image_tag))
        run_docker_command(
            "docker push {}:{}".format(tags.docker_full_image_name, image_tag)
        )


def prefetch_cached_images(tags):
    if docker_tags.running_on_azure_pipelines():
        print(print_separator)
        print(Fore.YELLOW + "PREFETCHING IMAGE")
        print(print_separator)
        tags.image_tag_to_use_for_cache = None

        for image_tag in tags.image_tags:
            print(
                Fore.YELLOW
                + "trying to prefetch {}:{}".format(
                    tags.docker_full_image_name, image_tag
                )
            )
            try:
                run_docker_command(
                    "docker pull {}:{}".format(tags.docker_full_image_name, image_tag)
                )
                tags.image_tag_to_use_for_cache = image_tag
                print(
                    Fore.GREEN
                    + "Found {}.  Using this for image cache".format(image_tag)
                )
                return
            except DockerSubprocessException:
                print(Fore.YELLOW + "Image not found in repository")


def get_description():
    return "build docker image for testing"


def set_command_args(parser):
    parser.description = get_description()
    parser.add_argument(
        "--language",
        help="language to build",
        type=str,
        required=True,
        choices=all_languages,
    )
    parser.add_argument(
        "--repo", help="repo with source", type=str, default=default_repo
    )
    parser.add_argument(
        "--commit", help="commit to apply (ref or branch)", type=str, default="master"
    )

    parser.add_argument(
        "--variant",
        help="Docker image variant (blank for default)",
        type=str,
        nargs="?",
        const="",
    )


def handle_command_args(args):
    if args.repo == default_repo:
        if args.language == "pythonv2":
            args.repo = "Azure/azure-iot-sdk-python"
        else:
            args.repo = "Azure/azure-iot-sdk-" + args.language
        print(Fore.YELLOW + "Repo not specified.  Defaulting to " + args.repo)

    tags = docker_tags.get_docker_tags_from_commit(
        args.language, args.repo, args.commit, args.variant
    )

    print(print_separator)
    print("repo = {}".format(tags.repo))
    print("commit_name = {}".format(tags.commit_name))
    print("commit_sha = {}".format(tags.commit_sha))

    prefetch_cached_images(tags)
    build_image(tags)
    tag_images(tags)
    push_images(tags)

    if not docker_tags.running_on_azure_pipelines():
        print(Fore.GREEN + "Done.  Deploy with the following command:")
        print(
            Fore.GREEN
            + "horton deploy iothub image {}:{}".format(
                tags.docker_full_image_name, tags.image_tags[0]
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="horton_build")
    set_command_args(parser)
    args = parser.parse_args()
    handle_command_args(args)
