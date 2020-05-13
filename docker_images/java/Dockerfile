from maven:3.6.3-jdk-8-slim

ENV MAVEN_CONFIG=/usr/share/maven/ref

RUN apt update && apt install --fix-missing -y \
  git 

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

EXPOSE 8080

# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .

COPY java/prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
WORKDIR /sdk
RUN git pull
RUN git checkout $HORTON_COMMIT_SHA

COPY java/patchfile /
# our base image might have some files checked out.  revert these.
RUN git reset HEAD && git checkout && git clean  -df
RUN if [ -s /patchfile ]; then git apply --index /patchfile; fi

RUN rm -r /sdk/iot-e2e-tests/edge-e2e
COPY java/wrapper /sdk/iot-e2e-tests/edge-e2e

COPY java/rebuild.sh /
RUN /rebuild.sh

ENTRYPOINT ["/usr/local/openjdk-8/bin/java", "-jar", "/sdk/iot-e2e-tests/edge-e2e/target/iot-edge-e2e-wrapper-1.0.0-with-deps.jar"]
