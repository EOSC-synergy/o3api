#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov
#

DOCKER_IMAGE=synergyimk/o3as:latest
DOCKER_CONTAINER="o3as-latest"

# Directories at your host for the raw data and outputs
HOST_DATA_RAW=$HOME/synergy/o3as/data/Ecmwf
HOST_DATA_OUT=$HOME/synergy/o3as/output

# mount necessary host directories inside container
DOCKER_OPTIONS="-v $HOST_DATA_RAW:/mnt/data/input -v $HOST_DATA_OUT:/mnt/data/output"

# define the command to run inside container
DOCKER_RUN_COMMAND="/srv/o3as/o3as/eosc.sh -i /mnt/data/input/ -o /mnt/data/output/ -b 1980 -e 1981 -l 50"

docker run --rm -ti ${DOCKER_OPTIONS} ${DOCKER_IMAGE} ${DOCKER_RUN_COMMAND}
