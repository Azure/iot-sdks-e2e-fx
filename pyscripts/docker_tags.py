# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license tagsrmation.
import os
import requests
import docker
from pprint import pprint


class DockerTags:
    def __init__(self):
        self.repo = None
        self.base_branch = None
        self.build_with_prid = None
        self.prid = None
        self.pr_url = None
        self.pr_ref = None
        self.commit_id_for_dockerfile = None
        self.commit_id_to_merge = None
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


def get_sha_from_commit(repo, commit):
    """
    given a GIT repo and a commit ID, return the SHA for that commit
    """
    response = requests.get(
        "https://api.github.com/repos/{}/git/refs/heads/{}".format(repo, commit)
    )
    if response.status_code == 200:
        return response.json()["object"]["sha"]
    elif response.status_code == 404:
        raise Exception("ERROR : Commit {} not found in repo {}".format(commit, repo))
    else:
        raise Exception(
            "unexpected result looking for commit {} in repo {} status = {} response = {}".format(
                commit, repo, response.status_code, response.json()
            )
        )


def get_sha_url_and_ref_from_prid(repo, prid):
    """
    given a GIT repo and a pull request ID, return the SHA, clone_url, and ref for that pull request
    """
    response = requests.get(
        "https://api.github.com/repos/{}/pulls/{}".format(repo, prid)
    )
    if response.status_code == 200:
        sha = response.json()["head"]["sha"]
        url = response.json()["head"]["repo"]["clone_url"]
        ref = response.json()["head"]["ref"]
        return (sha, url, ref)
    elif response.status_code == 405:
        raise Exception("ERROR : prid {} not found in repo {}".format(prid, repo))
    else:
        raise Exception(
            "unexpected result looking for prid {} in repo {} status = {} response = {}".format(
                prid, repo, response.status_code, response.json()
            )
        )


def sanitize_string(str):
    """
    sanitize a string by removing /, \, and -, and convert to PascalCase
    """
    for strip in ["/", "\\", "-"]:
        str = str.replace(strip, " ")
    components = str.split()
    return "".join(x.title() for x in components)


def shorten_sha(str):
    """
    return the short (7-character) version of a git sha
    """
    return str[:7]


def running_on_azure_pipelines():
    """
    return True if the script is running inside of an Azure pipeline
    """
    return "Build.BuildId" in os.environ


def _get_docker_tags_base(language, repo, branch_to_merge_to):
    tags = DockerTags()
    tags.docker_image_name = "{}-e2e".format(language)
    tags.docker_full_image_name = "{}/{}".format(
        tags.docker_repo, tags.docker_image_name
    )
    tags.language = language
    tags.repo = repo
    tags.base_branch = branch_to_merge_to
    tags.base_sha = get_sha_from_commit(repo, branch_to_merge_to)

    if running_on_azure_pipelines():
        tags.image_tags.insert(0, "vsts-{}".format(os.environ["Build.BuildId"]))
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
                shorten_sha(tags.base_sha),
            ),
        )
    else:
        tags.image_tags.insert(0, "latest")
    return tags


def get_docker_tags_for_commit(
    language, repo, branch_to_merge_to, commit_to_merge=None
):
    tags = _get_docker_tags_base(language, repo, branch_to_merge_to)

    tags.commit_to_merge = commit_to_merge or branch_to_merge_to
    tags.commit_id_for_dockerfile = tags.commit_to_merge
    tags.build_with_prid = "NO"
    tags.commit_sha = get_sha_from_commit(tags.repo, tags.commit_to_merge)
    if running_on_azure_pipelines():
        tags.image_tags.insert(
            0,
            "{}-{}-{}-{}-{}-{}".format(
                image_tag_prefix(),
                sanitize_string(tags.repo),
                sanitize_string(tags.base_branch),
                shorten_sha(tags.base_sha),
                sanitize_string(tags.commit_to_merge),
                shorten_sha(tags.commit_sha),
            ),
        )
    return tags


def get_docker_tags_for_prid(language, repo, branch_to_merge_to, prid_to_merge):
    tags = _get_docker_tags_base(language, repo, branch_to_merge_to)

    tags.prid = prid_to_merge
    tags.commit_id_for_dockerfile = tags.prid
    tags.build_with_prid = "YES"
    (tags.commit_sha, tags.pr_url, tags.pr_ref) = get_sha_url_and_ref_from_prid(
        tags.repo, tags.prid
    )
    if running_on_azure_pipelines():
        tags.image_tags.insert(
            0,
            "{}-{}-{}-{}-prid{}-{}".format(
                image_tag_prefix(),
                sanitize_string(tags.repo),
                sanitize_string(tags.base_branch),
                shorten_sha(tags.base_sha),
                tags.prid,
                shorten_sha(tags.commit_sha),
            ),
        )
    return tags


def get_docker_tags_from_environment():
    language = os.environ.get("LANGUAGE")
    repo = os.environ.get("AZURE_REPO")
    base_branch = os.environ.get("BRANCH_TO_MERGE_TO")

    if os.environ.get("BUILD_WITH_PRID") == "NO":
        commit_id = os.environ.get("COMMIT_ID")
        return get_docker_tags_for_commit(language, repo, base_branch, commit_id)
    else:
        prid = os.environ.get("COMMIT_ID")
        return get_docker_tags_for_prid(language, repo, base_branch, prid)
