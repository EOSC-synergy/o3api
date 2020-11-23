#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov
#

DOCKER_IMAGE=synergyimk/o3api
DOCKER_CONTAINER="o3api"

# Directories at your host for the raw data and outputs
HOST_DATA=$HOME/datasets/o3as-data

# mount necessary host directories inside container
DOCKER_OPTIONS="-v $HOST_DATA:/srv/o3api/data \
-p 5005:5005 \
-e WORKERS=1 \
-e DISABLE_AUTHENTICATION_AND_ASSUME_AUTHENTICATED_USER=yes"

# [debug] for debugging run bash (and comment the line with "[service]"
#docker run -ti --rm ${DOCKER_OPTIONS} ${DOCKER_IMAGE} /bin/bash

# [service] for service run directly default as daemon:
docker run -d --rm ${DOCKER_OPTIONS} ${DOCKER_IMAGE}
