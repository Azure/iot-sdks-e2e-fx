FROM mcr.microsoft.com/mirror/docker/library/ubuntu:18.04

RUN apt update \
  && apt install --fix-missing --no-install-recommends   -y \
    build-essential \
    cmake \
    curl \
    libcurl4-openssl-dev \
    libssl-dev \
    uuid-dev \
    pkg-config \
    git \
    gdbserver \
    openssh-server \
    ca-certificates \
    python \
    python-pip \
    iptables \
  &&  rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

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

RUN pip install --upgrade pip 

WORKDIR /system_control_app
COPY ./system_control_app .
RUN pip install -r requirements.txt
EXPOSE 8040

# force container rebuild when switching from master to main
RUN echo "switch to main" > /horton_tag.txt

ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .
RUN git submodule update --init

# copy the wrapper over and move restbed in place
COPY c/wrapper /wrapper
WORKDIR /wrapper/deps
RUN ln -s /restbed .

# and prebuild
COPY c/prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
WORKDIR /sdk
RUN git pull
RUN git checkout $HORTON_COMMIT_SHA

COPY c/patchfile /
# our base image might have some files checked out.  revert these.
RUN git reset HEAD && git checkout . && git clean  -df
RUN if [ -s /patchfile ]; then git apply --index /patchfile; fi

# must update submodules after applying the patch
RUN git submodule update --init

COPY c/rebuild.sh /
RUN /rebuild.sh

ENV HORTON_REPO=$HORTON_REPO
ENV HORTON_COMMIT_NAME=$HORTON_COMMIT_NAME
ENV HORTON_COMMIT_SHA=$HORTON_COMMIT_SHA

ENTRYPOINT ["/wrapper/build/edge_e2e_rest_server"]
