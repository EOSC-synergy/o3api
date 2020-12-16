# Dockerfile has three Arguments: base, tag, branch
# base - base image (default: ubuntu, optional: debian)
# tag - tag for base mage (default: 20.04, optional: stable-slim)
# branch - user repository branch to clone (default: master, other option: test)
#
# To build the image:
# $ docker build -t <dockerhub_user>/<dockerhub_repo> --build-arg arg=value .
# or using default args:
# $ docker build -t <dockerhub_user>/<dockerhub_repo> .

# set the base image. default is debian, optional ubuntu
ARG base=ubuntu
# set the tag (e.g. 20.04, latest, stable, stable-slim (for debian) )
ARG tag=20.04

# Base image, e.g. debian:stable or ubuntu:bionic
FROM ${base}:${tag}

LABEL maintainer='B.Esteban, T.Kerzenmacher, V.Kozlov (KIT)'
# REST API for the O3as service to process and plot O3 data

# What user branch to clone (!)
ARG branch=master

# Install system updates and tools
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
# Install system updates and tools
        git \
        nano \
        procps \
# Install system updates and tools
        #gcc \          # multidic needs in the case of debian
        #python3-dev \  # multidic needs in the case of debian
        python3-setuptools \
        python3-pip \
        python3-wheel && \
# Clean up & back to dialog front end
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=dialog
WORKDIR /srv

# Install user app:
RUN git clone --depth 1 -b $branch https://git.scc.kit.edu/synergy.o3as/o3api.git && \
# Install o3api
    cd o3api && \
    pip3 install --no-cache-dir -e . && \
    pip3 install --no-cache-dir gunicorn && \
# Clean up
    rm -rf /root/.cache/pip/* && \
    rm -rf /tmp/*
WORKDIR /srv/o3api

# Set environments
ENV PYTHONPATH=/srv/o3api
ENV LANG C.UTF-8

ENV ENABLE_HTTPS False
ENV O3API_WORKERS 1
ENV O3API_TIMEOUT 120

# Disable FLAAT authentication by default
ENV DISABLE_AUTHENTICATION_AND_ASSUME_AUTHENTICATED_USER yes

EXPOSE 5005

# Start default script
CMD ["/bin/bash", "/srv/o3api/start.sh"]
