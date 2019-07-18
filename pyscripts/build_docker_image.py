# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import docker
import json
import sys
import docker_tags
import argparse
import datetime
import colorama
from colorama import Fore

colorama.init(autoreset=True)

default_repo = "(Azure/azure-iot-sdk-BLAH)"
all_languages = ["c", "csharp", "python", "pythonpreview", "node", "java"]

parser = argparse.ArgumentParser(description="build docker image for testing")
parser.add_argument(
    "--language",
    help="language to build",
    type=str,
    required=True,
    choices=all_languages,
)
parser.add_argument("--repo", help="repo with source", type=str, default=default_repo)
parser.add_argument(
    "--commit", help="commit to apply (ref or branch)", type=str, default="master"
)
parser.add_argument(
    "--variant", help="Docker image variant (blank for default)", type=str, nargs="?", const=""
)
args = parser.parse_args()

if args.repo == default_repo:
    if args.language == "pythonpreview":
        args.repo = "Azure/azure-iot-sdk-python-preview"
    else:
        args.repo = "Azure/azure-iot-sdk-" + args.language
    print(Fore.YELLOW + "Repo not specified.  Defaulting to " + args.repo)

print_separator = "".join("/\\" for _ in range(80))

if sys.platform == 'win32':
    base_url = "tcp://127.0.0.1:2375"
else:
    base_url = "unix://var/run/docker.sock"

auth_config = {
    "username": os.environ["IOTHUB_E2E_REPO_USER"],
    "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"],
}


def get_dockerfile_directory(tags):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.normpath(os.path.join(script_dir, "../ci-wrappers/" + tags.language))


def print_filtered_docker_line(line):
    try:
        obj = json.loads(line.decode("utf-8"))
    except:
        print("".join([i if ord(i) < 128 else "#" for i in line.decode("utf-8")]))
    else:
        if "status" in obj:
            if "id" in obj:
                if obj["status"] not in [
                    "Waiting",
                    "Downloading",
                    "Verifying Checksum",
                    "Extracting",
                    "Preparing",
                    "Pushing",
                ]:
                    print("{}: {}".format(obj["status"], obj["id"]))
                else:
                    pass
            else:
                print(obj["status"])
        elif "error" in obj:
            print ("docker error: {}".format(line))
            raise Exception(obj["error"])
        elif "Step" in obj or "---" in obj:
            print("step: {}".format(obj).strip())
        elif obj == "\n":
            pass
        else:
            print("".join([i if ord(i) < 128 else "#" for i in line.decode("utf-8")]))


def build_image(tags):
    print(print_separator)
    print("BUILDING IMAGE")
    print(print_separator)

    force_flag = 0
    api_client = docker.APIClient(base_url=base_url)

    build_args = {
        "HORTON_REPO": tags.repo,
        "HORTON_COMMIT_NAME": tags.commit_name,
        "HORTON_COMMIT_SHA": tags.commit_sha,
    }

    if tags.image_tag_to_use_for_cache:
        cache_from = [
            tags.docker_full_image_name + ":" + tags.image_tag_to_use_for_cache
        ]
        print("using {} for cache".format(cache_from[0]))
    else:
        cache_from = []

    if tags.variant:
        dockerfile = "Dockerfile." + tags.variant
    else:
        dockerfile = "Dockerfile"

    print(
        Fore.YELLOW
        + "Building image for "
        + tags.docker_image_name
        + " using "
        + dockerfile
    )
    for line in api_client.build(
        path=get_dockerfile_directory(tags),
        tag=tags.docker_image_name,
        buildargs=build_args,
        cache_from=cache_from,
        dockerfile=dockerfile,
    ):
        try:
            sys.stdout.write(json.loads(line.decode("utf-8"))["stream"])
        except KeyError:
            print_filtered_docker_line(line)

def tag_images(tags):
    print(print_separator)
    print("TAGGING IMAGE")
    print(print_separator)

    api_client = docker.APIClient(base_url=base_url)

    print("Adding tags")
    for image_tag in tags.image_tags:
        print("Adding " + image_tag)
        api_client.tag(tags.docker_image_name, tags.docker_full_image_name, image_tag)


def push_images(tags):
    print(print_separator)
    print("PUSHING IMAGE")
    print(print_separator)

    api_client = docker.APIClient(base_url=base_url)

    for image_tag in tags.image_tags:
        print("Pushing {}:{}".format(tags.docker_full_image_name, image_tag))
        for line in api_client.push(
            tags.docker_full_image_name, image_tag, stream=True, auth_config=auth_config
        ):
            try:
                sys.stdout.write(json.loads(line.decode("utf-8"))["stream"])
            except:
                print_filtered_docker_line(line)


def prefetch_cached_images(tags):
    if docker_tags.running_on_azure_pipelines():
        print(print_separator)
        print(Fore.YELLOW + "PREFETCHING IMAGE")
        print(print_separator)
        tags.image_tag_to_use_for_cache = None

        api_client = docker.APIClient(base_url=base_url)

        for image_tag in tags.image_tags:
            print(
                Fore.YELLOW
                + "trying to prefetch {}:{}".format(
                    tags.docker_full_image_name, image_tag
                )
            )
            try:
                for line in api_client.pull(
                    tags.docker_full_image_name,
                    image_tag,
                    stream=True,
                    auth_config=auth_config,
                ):
                    print_filtered_docker_line(line)
                tags.image_tag_to_use_for_cache = image_tag
                print(
                    Fore.GREEN
                    + "Found {}.  Using this for image cache".format(image_tag)
                )
                return
            except docker.errors.APIError:
                print(Fore.YELLOW + "Image not found in repository")


tags = docker_tags.get_docker_tags_from_commit(
    args.language, args.repo, args.commit, args.variant
)

prefetch_cached_images(tags)
build_image(tags)
tag_images(tags)
push_images(tags)

if not docker_tags.running_on_azure_pipelines():
    print(Fore.GREEN + "Done.  Deploy with the following command:")
    print(
        Fore.GREEN
        + "./deploy-test-containers.sh --{} {}:{}".format(
            tags.language, tags.docker_full_image_name, tags.image_tags[0]
        )
    )    