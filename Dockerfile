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

# If to install JupyterLab
ARG jlab=true

# Install ubuntu updates and python related stuff
# link python3 to python, pip3 to pip, if needed
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y --no-install-recommends \
         binutils \
         curl \
         git \
         parallel \
         wget \
         python3-setuptools \
         python3-pip \
         python3-wheel && \ 
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /tmp/* && \
    if [ ! -e /usr/bin/pip ]; then \
       ln -s /usr/bin/pip3 /usr/bin/pip; \
    fi; \
    if [ ! -e /usr/bin/python ]; then \
       ln -s /usr/bin/python3 /usr/bin/python; \
    fi; \
    python --version && \
    pip --version

# Set LANG environment
ENV LANG C.UTF-8

# Set the working directory
WORKDIR /srv

# install rclone
RUN wget https://downloads.rclone.org/rclone-current-linux-amd64.deb && \
    dpkg -i rclone-current-linux-amd64.deb && \
    apt install -f && \
    mkdir /srv/.rclone/ && touch /srv/.rclone/rclone.conf && \
    rm rclone-current-linux-amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /tmp/*

ENV RCLONE_CONFIG=/srv/.rclone/rclone.conf

# Install JupyterLab
ENV JUPYTER_CONFIG_DIR /srv/o3as/.jupyter/
# Necessary for the Jupyter Lab terminal
ENV SHELL /bin/bash
RUN if [ "$jlab" = true ]; then \
       pip install --no-cache-dir jupyterlab ; \
    else echo "[INFO] Skip JupyterLab installation!"; fi

# Install CDO:
# libQt5 requires kernel >3.10
# use trick and remove this dependency in libQt5 (strip ..)
# https://askubuntu.com/questions/1034313/ubuntu-18-4-libqt5core-so-5-cannot-open-shared-object-file-no-such-file-or-dir
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y --no-install-recommends cdo && \
    strip --remove-section=.note.ABI-tag /usr/lib/x86_64-linux-gnu/libQt5Core.so.5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /tmp/* && \
    python --version && \
    pip --version

# Install user app:
#RUN git clone -b $branch https://git.scc.kit.edu/synergy.o3as/o3as.git && \
#    cd  o3as && \
#    pip install --no-cache-dir -e . && \
#    rm -rf /root/.cache/pip/* && \
#    rm -rf /tmp/* && \
#    cd ..

# Install user app:
# Use docker build gitlab_link
ADD $PWD /srv/o3as/
RUN cd /srv/o3as && pip install --no-cache-dir -r requirements.txt

# Open Jupyter port
EXPOSE 8888

# Start default script
CMD ["cdo", "--version"]
