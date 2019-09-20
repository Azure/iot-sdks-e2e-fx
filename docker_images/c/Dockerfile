FROM ubuntu:18.04

# common to C and Python
RUN apt update \
  && apt install --fix-missing --no-install-recommends   -y \
    build-essential \
    wget \
    vim \
    cmake \
    curl \
    libcurl4-openssl-dev \
    libssl-dev \
    uuid-dev \
    pkg-config \
    git

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

# C only

RUN apt install -y \
    gdbserver \
    openssh-server

EXPOSE 8082
EXPOSE 22

# get ready for ssh keys
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh && touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys


# make a key that we can use to connect to SSH and authorize it.
# people who want to use SSH can use docker cp to get the key out of the container
RUN ssh-keygen -b 2048 -t rsa -f /root/.ssh/remote-debug -q -N ""
RUN cat /root/.ssh/remote-debug.pub > /root/.ssh/authorized_keys

# fetch restbed early.  This never changes, so we grab it here.
# submodules are huge, so we do everything in one command (one layer) and rm -r as much as possible
WORKDIR /restbed
RUN git clone https://github.com/Corvusoft/restbed . \
    && git checkout 1b43b9a \
    && git submodule update --init --recursive \
    && rm -r .git \
    && rm -r dependency/openssl/fuzz \
    && rm -r dependency/openssl/apps \
    && rm -r dependency/openssl/doc \
    && rm -r dependency/openssl/test \
    && rm -r dependency/asio/asio/src/doc \
    && rm -r dependency/asio/asio/src/tests \
    && rm -r dependency/asio/asio/src/examples


ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .
RUN git submodule update --init

# copy the wrapper over and move restbed in place
COPY wrapper /wrapper
WORKDIR /wrapper/deps
RUN if [ -d restbed ]; then rm -r restbed; fi
RUN ln -s /restbed .

# and prebuild
COPY ./prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
WORKDIR /sdk
RUN git pull
RUN git checkout $HORTON_COMMIT_SHA

COPY ./patchfile /
# our base image might have some files checked out.  revert these.
RUN git reset HEAD && git checkout && git clean  -df
RUN if [ -s /patchfile ]; then git apply --index /patchfile; fi

# must update submodules after applying the patch
RUN git submodule update --init

COPY ./rebuild.sh /
RUN /rebuild.sh

ENTRYPOINT ["/wrapper/build/edge_e2e_rest_server"]
