# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import docker
import json
import sys
import docker_tags
import argparse
import datetime

parser = argparse.ArgumentParser(description="build docker image for testing")
parser.add_argument("--language", help="language to build", type=str, required=True)
parser.add_argument("--repo", help="repo with source", type=str, required=True)
parser.add_argument(
    "--commit", help="commit to apply (ref or branch)", type=str, required=True
)
args = parser.parse_args()

print_separator = "".join("/\\" for _ in range(80))

auth_config = {
    "username": os.environ["IOTHUB_E2E_REPO_USER"],
    "password": os.environ["IOTHUB_E2E_REPO_PASSWORD"],
}


def get_dockerfile_directory(tags):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.normpath(os.path.join(script_dir, "../ci-wrappers/" + tags.language))


def build_image(tags):
    print(print_separator)
    print("BUILDING IMAGE")
    print(print_separator)

    force_flag = 0
    if os.stat(get_dockerfile_directory(tags) + "/source.tar.gz").st_size > 0:
        print("source.tar.gz exists.  Setting force flag.")
        force_flag = datetime.datetime.now().timestamp()

    api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
    build_args = {
        "HORTON_REPO": tags.repo,
        "HORTON_COMMIT_NAME": tags.commit_name,
        "HORTON_COMMIT_SHA": tags.commit_sha,
        "HORTON_FORCEFLAG": str(force_flag),
    }

    if tags.image_tag_to_use_for_cache:
        cache_from = [
            tags.docker_full_image_name + ":" + tags.image_tag_to_use_for_cache
        ]
        print("using {} for cache".format(cache_from[0]))
    else:
        cache_from = []

    print("Building image for " + tags.docker_image_name)
    for line in api_client.build(
        path=get_dockerfile_directory(tags),
        tag=tags.docker_image_name,
        buildargs=build_args,
        cache_from=cache_from,
    ):
        try:
            sys.stdout.write(json.loads(line.decode("utf-8"))["stream"])
        except KeyError:
            sys.stdout.write(line.decode("utf-8") + "\n")


def tag_images(tags):
    print(print_separator)
    print("TAGGING IMAGE")
    print(print_separator)
    api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
    print("Adding tags")
    for image_tag in tags.image_tags:
        print("Adding " + image_tag)
        api_client.tag(tags.docker_image_name, tags.docker_full_image_name, image_tag)


def push_images(tags):
    print(print_separator)
    print("PUSHING IMAGE")
    print(print_separator)
    api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
    for image_tag in tags.image_tags:
        print("Pushing {}:{}".format(tags.docker_full_image_name, image_tag))
        for line in api_client.push(
            tags.docker_full_image_name, image_tag, stream=True, auth_config=auth_config
        ):
            print(line)


def prefetch_cached_images(tags):
    if docker_tags.running_on_azure_pipelines():
        print(print_separator)
        print("PREFETCHING IMAGE")
        print(print_separator)
        tags.image_tag_to_use_for_cache = None
        api_client = docker.APIClient(base_url="unix://var/run/docker.sock")
        for image_tag in tags.image_tags:
            print(
                "trying to prefetch {}:{}".format(
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
                    print(line)
                tags.image_tag_to_use_for_cache = image_tag
                print("Found {}.  Using this for image cache".format(image_tag))
                return
            except docker.errors.APIError:
                print("Image not found in repository")


tags = docker_tags.get_docker_tags_from_commit(args.language, args.repo, args.commit)

prefetch_cached_images(tags)
build_image(tags)
tag_images(tags)
push_images(tags)

if not docker_tags.running_on_azure_pipelines():
    print("Done.  Deploy with the following command:")
    print(
        "./deploy-test-containers.sh --{} {}:{}".format(
            tags.language, tags.docker_full_image_name, tags.image_tags[0]
        )
    )
