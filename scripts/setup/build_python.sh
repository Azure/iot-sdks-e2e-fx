#!/bin/bash
#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

if [ "${BASH_SOURCE-}" = "$0" ]; then
    echo "You must source this script: \$ source $0" >&2
    exit 33
fi

RUNTIME=3.7.7

sudo apt-get install -y make build-essential zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev dos2unix libssl1.0-dev dos2unix
[ $? -eq 0 ] || { echo "APT failed"; exit 1; }

curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
[ $? -eq 0 ] || { echo "failed installing pyenv"; exit 1; }

cd ${HOME}/.pyenvZZ
[ $? -eq 0 ] || { echo "failed cd ${HOME}/.pyenv"; exit 1; }

# pyenv-installer gives us CRLF when we just want LF.  Force LF
find -type f -a -not \( -path './versions/*' \) -print0 | \
    xargs -0 -I @@ bash -c 'file "$@" | grep ASCII &>/dev/null && dos2unix $@' -- @@

export PATH="${HOME}/.pyenv/bin:${PATH}"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
eval "$(pyenv init -)"

# echo calling pyenv install -s $RUNTIME
# pyenv install -g -s $RUNTIME
# [ $? -eq 0 ] || { echo "failed installing Python $RUNTIME"; build_failure_help; exit 1; }

pyenv shell $RUNTIME
[ $? -eq 0 ] || { echo "failed calling pyenv to use Python $RUNTIME for this script"; exit 1; }

python -m pip install --upgrade pip
[ $? -eq 0 ] || { echo "failed upgrading PIP for Python $RUNTIME"; exit 1; }

python -m pip install virtualenv
[ $? -eq 0 ] || { echo "failed installing virtualenv for Python $RUNTIME"; exit 1; }

python -m virtualenv "${HOME}/env/Python-${RUNTIME}"
[ $? -eq 0 ] || { echo "failed setting up a virtual environment for Python $RUNTIME"; exit 1; }


echo Success!
echo
echo "Use the following commands to switch python versions (or use the aliases below):"
echo "source ~/env/Python-${RUNTIME}/bin/activate"
echo
echo "Add the following to your .bashrc file:"
echo "export PATH=\"${HOME}/.pyenv/bin:\$PATH\""
echo "eval \"\$(pyenv init -)\""
echo "eval \"\$(pyenv virtualenv-init -)\""
echo "alias pip='python -m pip $@'"
echo "alias py-${RUNTIME}='source ~/env/Python-${RUNTIME}/bin/activate'"


source ~/env/Python-${RUNTIME}/bin/activate





