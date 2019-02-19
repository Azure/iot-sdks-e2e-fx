FROM microsoft/dotnet:2.2-sdk

# Install system components for powershell install
RUN apt update \
  && apt install --fix-missing -y \
    vim \
    git \
    curl

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

EXPOSE 80/tcp

# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .
RUN git submodule update --init --recursive
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
COPY wrapper /wrapper
run /rebuild.sh

WORKDIR /app
ENTRYPOINT ["dotnet", "IO.Swagger.dll"]
