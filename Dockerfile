# Dockerfile has 2 Arguments: base, tag 
# base - base image (default: debian, optional: ubuntu)
# tag - tag for base mage (default: stable-slim)
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

# Install system updates and tools
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        binutils \
        curl \
        parallel \
        wget

# install python3
RUN apt-get install -y --no-install-recommends \
        python3-setuptools \
        python3-pip \
        python3-wheel &&\
    python3 --version && \
    pip3 --version

# Install CDO:
# libQt5 requires kernel >3.10
# use trick and remove this dependency in libQt5 (strip ..)
# https://askubuntu.com/questions/1034313/ubuntu-18-4-libqt5core-so-5-cannot-open-shared-object-file-no-such-file-or-dir
RUN apt-get install -y --no-install-recommends cdo && \
    strip --remove-section=.note.ABI-tag /usr/lib/x86_64-linux-gnu/libQt5Core.so.5 && \
    cdo --version

# Install o3as requirements
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt 

# Clean up & back to dialog front end
RUN apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/* && \
    rm -rf /root/.cache/pip/*
ENV DEBIAN_FRONTEND=dialog

# Set LANG environment
ENV LANG C.UTF-8

# Set the working directory
WORKDIR /srv
COPY src src
RUN mkdir data && \ 
    mkdir output


# Start default script
CMD ["cdo", "--version"]

