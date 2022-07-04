#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov
#

# o3api docker image
# for all tags, check https://hub.docker.com/r/o3as/o3api/tags
DOCKER_IMAGE=o3as/o3api:latest
DOCKER_CONTAINER="o3api"

# Directories at your host for O3as raw data
# Skimmed data used by API, are usually placed in the "Skimmed" subdirectory
HOST_DATA=$HOME/datasets/o3as-data

# mount necessary host directories inside container
# provide environment variables
# pass the port to run on
DOCKER_OPTIONS="\
-v $HOST_DATA:/o3as-data \
-e O3AS_DATA_BASEPATH=/o3as-data/Skimmed \
-e WORKERS=1 \
-p 5005:5005"

# [debug] for debugging run bash (and comment the line with "[service]"
#docker run -ti --rm ${DOCKER_OPTIONS} --name ${DOCKER_CONTAINER} ${DOCKER_IMAGE} /bin/bash

# [service] for service run directly default as daemon:
docker run -d --rm ${DOCKER_OPTIONS} --name ${DOCKER_CONTAINER} ${DOCKER_IMAGE}
