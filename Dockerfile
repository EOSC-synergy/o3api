# Dockerfile has three Arguments: base, tag, branch
# base - base image (default: debian, optional: ubuntu)
# tag - tag for base mage (default: stable-slim)
# branch - user repository branch to clone (default: master, other option: test)
#
# To build the image:
# $ docker build -t <dockerhub_user>/<dockerhub_repo> --build-arg arg=value .
# or using default args:
# $ docker build -t <dockerhub_user>/<dockerhub_repo> .

# set the base image. default is debian, optional ubuntu
ARG base=debian
# set the tag (e.g. latest, stable, stable-slim : for debian)
ARG tag=stable-slim

# Base image, e.g. debian:stable or ubuntu:bionic
FROM ${base}:${tag}

LABEL maintainer='B.Esteban, T.Kerzenmacher, V.Kozlov (KIT)'
# o3as scripts to process data

# What user branch to clone (!)
ARG branch=master

# Install system updates and tools
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
# Install system updates and tools
        binutils \
        parallel \
        git \
# Install system updates and tools
        python3-setuptools \
        python3-pip \
        python3-wheel \
# Install CDO:
# libQt5 requires kernel >3.10
# use trick and remove this dependency in libQt5 (strip ..)
# https://askubuntu.com/questions/1034313/ubuntu-18-4-libqt5core-so-5-cannot-open-shared-object-file-no-such-file-or-dir
        cdo && \
    strip --remove-section=.note.ABI-tag /usr/lib/x86_64-linux-gnu/libQt5Core.so.5 && \
# Clean up & back to dialog front end
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=dialog
WORKDIR /srv

# Install user app:
RUN git clone --depth 1 -b $branch https://git.scc.kit.edu/synergy.o3as/o3as.git && \
    cd o3as && \
# Install o3as
    pip3 install --no-cache-dir -e . && \
# Clean up
    rm -rf /root/.cache/pip/* && \
    rm -rf /tmp/*
WORKDIR /srv/o3as

# Set LANG environment
ENV LANG C.UTF-8

# Start default script
CMD ["cdo", "--version"]
