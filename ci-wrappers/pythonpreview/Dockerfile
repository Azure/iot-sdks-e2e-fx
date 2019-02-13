from python:3.6

RUN apt update \
 && apt install -y \
    git \
    vim

RUN git config --global user.email "you@example.com" \
&&  git config --global user.name "Your Name" \
&&  git config --global core.eol lf

EXPOSE 8080

# wrapper requirements almost never change.  Install those first.
WORKDIR /wrapper
COPY ./wrapper/requirements.txt .
RUN pip install -r requirements.txt


# phase 1: grab the base branch and run prebuild
ARG HORTON_REPO
ARG HORTON_BASE_BRANCH
WORKDIR /sdk
RUN git clone https://github.com/$HORTON_REPO -b $HORTON_BASE_BRANCH .
COPY ./prebuild.sh /
RUN /prebuild.sh

# phase 2: grab the code we want to test and rebuild
ARG HORTON_SHA
ARG HORTON_FORCEFLAG
VOLUME /t
COPY ./source.tar.gz /t/
COPY ./fetch.sh /
RUN /fetch.sh /t
COPY ./rebuild.sh /
RUN /rebuild.sh

WORKDIR /wrapper
COPY ./wrapper .
RUN pip install -r requirements.txt
RUN python setup.py install

ENTRYPOINT ["python", "-u", "-m", "swagger_server"]

