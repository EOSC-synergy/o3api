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

UDOCKER_CONTAINER="o3as-ubuntu"

##### If you need to pull NEW image and CREATE Container, do first:
udocker pull synergyimk/o3as:ubuntu
udocker create --name=o3as-ubuntu synergyimk/o3as:ubuntu
# NB: creating container may take 5-10 minutes...
#may change execmode:
#udocker setup --execmode=F3 o3as-ubuntu
#####

HOST_DATA_RAW=$HOME/synergy/o3as/Data/raw/Ecmwf
HOST_DATA_OUT=$HOME/synergy/o3as/Data/output

UDOCKER_OPTIONS="-v $HOST_DATA_RAW:/mnt/data/input -v $HOST_DATA_OUT:/mnt/data/output"
UDOCKER_RUN_COMMAND="/srv/o3as/eosc.sh -i /mnt/data/input/ -o /mnt/data/output/ -b 1980 -e 1981 -l 50"

udocker run  ${UDOCKER_OPTIONS} ${UDOCKER_CONTAINER} ${UDOCKER_RUN_COMMAND}
