# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license tagsrmation.
import os
import docker
import github


class DockerTags:
    def __init__(self):
        self.repo = None
        self.base_branch = "master"
        self.commit_name = None
        self.commit_sha = None
        self.langauge = None
        if running_on_azure_pipelines():
            self.docker_repo = os.environ.get("IOTHUB_E2E_REPO_ADDRESS")
        else:
            self.docker_repo = "localhost:5000"
        self.image_tags = []
        self.image_tag_to_use_for_cache = None


def image_tag_prefix():
    """
    Return a prefix to use on all tags
    """
    # put the prefix as an attribute on this function to make it
    # behave like a function-scope static variable that we only
    # initialize once
    if not hasattr(image_tag_prefix, "prefix"):
        client = docker.from_env()
        version = client.version()
        image_tag_prefix.prefix = "{}-{}-dockerV{}".format(
            version["Os"], version["Arch"], version["Version"].split(".")[0]
        )
    return image_tag_prefix.prefix


def shorten_sha(str):
    """
    return the short (7-character) version of a git sha
    """
    return str[:7]


def sanitize_string(str):
    """
    sanitize a string by removing /, \\, and -, and convert to PascalCase
    """
    for strip in ["/", "\\", "-"]:
        str = str.replace(strip, " ")
    components = str.split()
    return "".join(x.title() for x in components)


def running_on_azure_pipelines():
    """
    return True if the script is running inside of an Azure pipeline
    """
    return "BUILD_BUILDID" in os.environ


def get_commit_name(commit):
    if commit.startswith("refs/heads/"):
        return commit.split("/")[2]
    elif commit.startswith("refs/pull/"):
        return "PR" + commit.split("/")[2]
    else:
        return commit


def get_docker_tags_from_commit(language, repo, commit):
    tags = DockerTags()
    tags.docker_image_name = "{}-e2e-v2".format(language)
    tags.docker_full_image_name = "{}/{}".format(
        tags.docker_repo, tags.docker_image_name
    )
    tags.language = language
    tags.repo = repo
    tags.commit_name = get_commit_name(commit)
    tags.commit_sha = github.get_sha_from_commit(repo, commit)

    if running_on_azure_pipelines():
        tags.image_tags.insert(0, "vsts-{}".format(os.environ["BUILD_BUILDID"]))
        tags.image_tags.insert(
            0,
            "{}-{}-{}".format(
                image_tag_prefix(),
                sanitize_string(tags.repo),
                sanitize_string(tags.base_branch),
            ),
        )
        tags.image_tags.insert(
            0,
            "{}-{}-{}-{}".format(
                image_tag_prefix(),
                sanitize_string(tags.repo),
                sanitize_string(tags.base_branch),
                sanitize_string(tags.commit_name),
            ),
        )
    else:
        tags.image_tags.insert(0, "latest")
    return tags
