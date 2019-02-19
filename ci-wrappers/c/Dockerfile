FROM ubuntu:18.04

# common to C and Python
RUN apt update \
  && apt install --fix-missing -y \
    build-essential \
    wget \
    vim \
    cmake \
    curl \
    libcurl4-openssl-dev \
    libssl-dev \
    uuid-dev \
    pkg-config \
    git \
    valgrind

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

# C only

EXPOSE 8082

# fetch restbed early.  This never changes, so we grab it here.
WORKDIR /restbed
RUN git clone https://github.com/Corvusoft/restbed .
RUN git checkout 1b43b9a
RUN git submodule update --init --recursive

# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .
RUN git submodule update --init --recursive

# copy the wrapper over and move restbed in place
COPY wrapper /wrapper
WORKDIR /wrapper/deps
RUN if [ -d restbed ]; then rm -r restbed; fi
RUN ln -s /restbed .

# and prebuild
COPY ./prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_SHA
ARG HORTON_COMMIT_NAME
ARG HORTON_FORCEFLAG
VOLUME /t
COPY ./source.tar.gz /t/
COPY ./fetch.sh /
RUN /fetch.sh /t
COPY ./rebuild.sh /
RUN /rebuild.sh

ENTRYPOINT ["/wrapper/build/edge_e2e_rest_server"]
