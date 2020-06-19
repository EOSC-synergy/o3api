#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov
#

#### if udocker is not installed, do:
# curl https://raw.githubusercontent.com/indigo-dc/udocker/master/udocker.py > udocker
# chmod u+rx ./udocker
# mv udocker $HOME/.local/bin # (or something in your PATH)
# udocker install
##
# More INFO: https://github.com/indigo-dc/udocker/blob/master/doc/installation_manual.md
####

DOCKER_IMAGE=synergyimk/o3as:deb10-cdo196
DOCKER_CONTAINER="o3as-deb10-cdo196"

##### If you need to pull NEW image and CREATE Container, do first:
#docker pull ${DOCKER_IMAGE}
#udocker pull synergyimk/o3as:ubuntu
#docker create --name=${DOCKER_CONTAINER} ${DOCKER_IMAGE}
#udocker create --name=o3as-ubuntu synergyimk/o3as:ubuntu
# NB: creating container may take 5-10 minutes...
#may change execmode:
#udocker setup --execmode=F3 o3as-ubuntu
#####

# Best is to create a soft link to folder were the data are in ./Data/raw
# For example `ln -s /home/<user>/O3as/Data/Ecmwf ./Data/raw/Ecmwf`
HOST_DATA_RAW=`readlink -f ./Data/raw/Ecmwf`
HOST_DATA_OUT=./Data/output

DOCKER_OPTIONS="-v $HOST_DATA_RAW:/mnt/data/input -v $HOST_DATA_OUT:/mnt/data/output"
DOCKER_RUN_COMMAND="/srv/o3as/eosc.sh -i /mnt/data/input/ -o /mnt/data/output/ -b 1980 -e 1981 -l 50"

docker run  ${DOCKER_OPTIONS} ${DOCKER_IMAGE} ${DOCKER_RUN_COMMAND}


