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

COPY ./rebuild.sh /

# Set these early.  If these change, we want to rebuild starting here to set a baseline which includes 
# as many dependencies as we can
ARG AZURE_REPO
ARG BRANCH_TO_MERGE_TO

WORKDIR /sdk
RUN git clone https://github.com/$AZURE_REPO -b $BRANCH_TO_MERGE_TO .
RUN git submodule update --init --recursive

# check the latest SHA.  If it's changed, fetch again
# this seems redundant, but we're setting another baseline here
# we have to re-fetch because the last fetch might be from a cached image that was built in the past
RUN curl get https://api.github.com/repos/$AZURE_REPO/git/refs/heads/$BRANCH_TO_MERGE_TO | grep "sha" > sha.txt
# use git reset --hard in case BRANCH_TO_MERGE_TO has been rebased since the clone above.
RUN git fetch origin && git reset --hard origin/$BRANCH_TO_MERGE_TO
run git submodule update --init --recursive

# these ARG lines are intentionally after the git clone so we can use the cached clone even when these args change
ARG BUILD_WITH_PRID
ARG COMMIT_ID
ARG PR_SOURCE_URL
ARG PR_SOURCE_REF
ARG COMMIT_SHA

RUN echo BUILD_WITH_PRID=$BUILD_WITH_PRID
RUN echo COMMIT_ID=$COMMIT_ID
RUN echo PR_SOURCE_URL=$PR_SOURCE_URL
RUN echo PR_SOURCE_REF=$PR_SOURCE_REF
RUN echo COMMIT_SHA=$COMMIT_SHA

# finally, re-fetch so we can merge our branch in
run git pull
RUN \
  if [ $BUILD_WITH_PRID = "NO" ]; then \
    git merge --ff --strategy=recursive origin/$COMMIT_ID ; \
  else \
    git fetch $PR_SOURCE_URL $PR_SOURCE_REF:pullsource && \
    git merge --ff --strategy=recursive pullsource ; \
  fi
RUN git submodule update --init --recursive

# copy the wrapper over and move restbed in place
COPY wrapper /wrapper
WORKDIR /wrapper/deps
RUN if [ -d restbed ]; then rm -r restbed; fi
RUN ln -s /restbed .

# finally we can build
RUN /rebuild.sh

ENTRYPOINT ["/wrapper/build/edge_e2e_rest_server"]
