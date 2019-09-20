FROM microsoft/dotnet:2.2-sdk

RUN apt update \
  && apt install --fix-missing -y \
    rsync \
    vim \
    git \
    curl \
    unzip \
    openssh-server \
  && apt clean

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name"

EXPOSE 80/tcp
EXPOSE 22/tcp

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

COPY wrapper /wrapper

COPY ./prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
RUN git pull 
RUN git checkout $HORTON_COMMIT_SHA

COPY ./patchfile /
# our base image might have some files checked out.  revert these.
RUN git reset HEAD && git checkout && git clean  -df
RUN if [ -s /patchfile ]; then git apply --index /patchfile; fi

COPY ./rebuild.sh /
run /rebuild.sh

WORKDIR /app
ENTRYPOINT ["dotnet", "IO.Swagger.dll"]
