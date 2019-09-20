from ubuntu:18.04

# common to C and Python
RUN apt update \
  && apt install --fix-missing -y \
    rsync \
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

# python only
RUN apt install --fix-missing -y \
    python3 \
    python3-pip \
    python3.6-dev \
    libboost-dev \
    libboost-python-dev \
    python3.6-dbg

EXPOSE 8080

# this block, along with python3.6-dbg above allows us to use gdb for python debugging (py-bt command, etc)
WORKDIR /root/.config/gdb
RUN wget https://hg.python.org/cpython/rawfile/3.6/Tools/gdb/libpython.py
RUN echo 'python \n\
import gdb \n\
import sys \n\
import os \n\
sys.path.insert(0, os.path.expanduser("~/.config/gdb")) \n\
def setup_python(event): \n\
    import libpython \n\
gdb.events.new_objfile.connect(setup_python) \n\
end\n\
' > /root/.gdbinit

# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO .
RUN git submodule update --init --recursive

COPY ./prebuild.sh /
RUN /prebuild.sh

WORKDIR /wrapper
COPY ./wrapper .

# phase 2: grab the code we want to test and rebuild
ARG HORTON_COMMIT_NAME
ARG HORTON_COMMIT_SHA
WORKDIR /sdk
RUN git pull 
RUN git checkout $HORTON_COMMIT_SHA

COPY ./patchfile /
# our base image might have some files checked out.  revert these.
RUN git reset HEAD && git checkout && git clean  -df
RUN if [ -s /patchfile ]; then git apply --index /patchfile; fi

# must update submodules after applying the patch
RUN git submodule update --init --recursive

COPY ./rebuild.sh /
RUN /rebuild.sh

WORKDIR /wrapper
RUN pip3 install -r requirements.txt
RUN python3 setup.py install

ENTRYPOINT ["python3", "-u", "-m", "swagger_server"]

