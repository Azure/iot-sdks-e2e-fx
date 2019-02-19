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

# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .
RUN git submodule update --init --recursive
COPY ./prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
ARG HORTON_FORCEFLAG
VOLUME /t
COPY ./source.tar.gz /t/
COPY ./fetch.sh /
RUN /fetch.sh /t
COPY ./rebuild.sh /
RUN /rebuild.sh

ENTRYPOINT ["/usr/bin/java", "-jar", "/sdk/iot-e2e-tests/edge-e2e/target/iot-edge-e2e-wrapper-1.0.0-with-deps.jar"]
