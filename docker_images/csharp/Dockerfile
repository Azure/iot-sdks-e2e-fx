FROM mcr.microsoft.com/dotnet/sdk:5.0-cbl-mariner1.0

RUN yum install -y \
    git \
    curl \
    unzip \
    openssh-server 

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

EXPOSE 80/tcp
EXPOSE 22/tcp

# install aspnetcore 3.1 runtime
RUN curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin -Channel 3.1 -Runtime aspnetcore


# get ready for ssh keys
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh && touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys

# make a key that we can use to connect to SSH and authorize it.  
# people who want to use SSH can use docker cp to get the key out of the container
RUN ssh-keygen -b 2048 -t rsa -f /root/.ssh/remote-debug -q -N ""
RUN cat /root/.ssh/remote-debug.pub > /root/.ssh/authorized_keys

# install vsdbg
RUN curl -sSL https://aka.ms/getvsdbgsh | bash /dev/stdin -v latest -l /vsdbg

# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .

COPY csharp/wrapper/src/*.csproj /wrapper/src/
workdir /wrapper/src
RUN dotnet restore

COPY csharp/wrapper /wrapper

COPY csharp/prebuild.sh /
RUN /prebuild.sh


# phase 2: grab the code we want to test and rebuild
WORKDIR /sdk
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
RUN git pull 
RUN git checkout $HORTON_COMMIT_SHA

COPY csharp/patchfile /
# our base image might have some files checked out.  revert these.
RUN git reset HEAD && git checkout . && git clean  -df
RUN if [ -s /patchfile ]; then git apply --index /patchfile; fi

COPY csharp/rebuild.sh /
run /rebuild.sh

ENV HORTON_REPO=$HORTON_REPO
ENV HORTON_COMMIT_NAME=$HORTON_COMMIT_NAME
ENV HORTON_COMMIT_SHA=$HORTON_COMMIT_SHA

WORKDIR /app
ENTRYPOINT ["/root/.dotnet/dotnet", "IO.Swagger.dll"]
