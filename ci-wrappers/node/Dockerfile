FROM node:6-slim

RUN apt update \
  && apt install --fix-missing -y \
    vim \
    git

RUN npm install lerna -g

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

env DEBUG=rhea*,azure*
EXPOSE 9229
EXPOSE 8080

# Set these early.  If these change, we want to rebuild starting here to set a baseline which includes 
# as many dependencies as we can
ARG AZURE_REPO
ARG BASE_BRANCH

WORKDIR /sdk
RUN git clone https://github.com/$AZURE_REPO -b $BASE_BRANCH .

COPY ./rebuild.sh /
RUN /rebuild.sh

# now check the latest SHA.  If it's changed, fetch and rebuild.
# this seems redundant, but we're setting another baseline here
# we have to re-fetch because the last fetch might be from a cached image that was built in the past
ARG BASE_SHA
RUN git fetch origin && git reset --hard origin/$BASE_BRANCH
run /rebuild.sh

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

# we have to fetch again because the baseline images above might be from the past
run git fetch origin
RUN \
  if [ $BUILD_WITH_PRID = "NO" ]; then \
    git merge --ff --strategy=recursive origin/$COMMIT_ID ; \
  else \
    git fetch $PR_SOURCE_URL $PR_SOURCE_REF:pullsource && \
    git merge --ff --strategy=recursive pullsource ; \
  fi
RUN /rebuild.sh

ENTRYPOINT ["/usr/local/bin/node", "/sdk/edge-e2e/wrapper/nodejs-server-server/index.js"]
