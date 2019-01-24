FROM maven:3.3-jdk-8

# Move the default M2 directory somewhere that gets persisted with the package.
ENV MAVEN_CONFIG=/usr/share/maven/ref

RUN apt update \
 && apt install --fix-missing -y \
  git \
  vim

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

EXPOSE 8080

# Set these early.  If these change, we want to rebuild starting here to set a baseline which includes
# as many dependencies as we can
ARG AZURE_REPO
ARG BRANCH_TO_MERGE_TO

WORKDIR /sdk
RUN git clone https://github.com/$AZURE_REPO -b $BRANCH_TO_MERGE_TO .
RUN git pull

COPY ./rebuild.sh /
RUN /rebuild.sh

# now check the latest SHA.  If it's changed, fetch and rebuild.
# this seems redundant, but we're setting another baseline here
# we have to re-fetch because the last fetch might be from a cached image that was built in the past
RUN curl get https://api.github.com/repos/$AZURE_REPO/git/refs/heads/$BRANCH_TO_MERGE_TO | grep "sha" > sha.txt
# use git reset --hard in case BRANCH_TO_MERGE_TO has been rebased since the clone above.
RUN git fetch origin && git reset --hard origin/$BRANCH_TO_MERGE_TO
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

run /rebuild.sh

ENTRYPOINT ["/usr/bin/java", "-jar", "/sdk/iot-e2e-tests/edge-e2e/target/iot-edge-e2e-wrapper-1.0.0-with-deps.jar"]
