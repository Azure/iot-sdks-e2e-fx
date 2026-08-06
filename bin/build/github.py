# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license tagsrmation.
import os
import subprocess


def get_sha_from_commit(repo, commit):
    """
    given a GIT repo and a commit ID, return the SHA for that commit

    This resolves the ref over the git protocol rather than through
    api.github.com.  The REST API allows only 60 anonymous requests per hour
    per source IP, shared by every job running on that hosted agent, so a busy
    hour exhausts the budget and the build dies with a 403 that has nothing to
    do with the change under test.  git ls-remote is not part of that budget
    and needs no credential for a public repo, so there is no token to issue,
    authorize, rotate or expire.
    """
    if not commit.startswith("refs/"):
        commit = "refs/heads/" + commit

    url = "https://github.com/{}".format(repo)
    # A repo that is missing or private makes git ask for credentials on the
    # terminal, which would hang the build rather than fail it.
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        output = subprocess.check_output(
            ["git", "ls-remote", url, commit],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env,
        )
    except subprocess.CalledProcessError as e:
        raise Exception(
            "ERROR : could not reach repo {} to resolve {}: {}".format(
                repo, commit, e.output.strip()
            )
        )

    # Output is "<sha>\t<ref>" per line.  Match the ref exactly: ls-remote
    # treats its argument as a pattern, so a loose one could return several.
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == commit:
            return parts[0]

    raise Exception("ERROR : Commit {} not found in repo {}".format(commit, repo))
