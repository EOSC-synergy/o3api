# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under its License. Please, see the LICENSE file
#

# Script to create metadata.yaml for datasources
# Inputs: 
#    * Directory with skimmed data (O3AS_DATA_BASEPATH)
#    * CSV file exported from the GoogleSheet "Data sources"
#

import os
import pandas as pd
import yaml
import xarray as xr

debug = True

# Directory for Skimmed data
O3AS_DATA_BASEPATH = os.getenv('O3AS_DATA_BASEPATH', "/srv/o3api/data/Skimmed/")

# Plot types
TCO3 = 'tco3_zm'
TCO3Return = 'tco3_return'
VMRO3 = 'vmro3_zm'
PLOT_TYPES = [TCO3, TCO3Return, VMRO3]

# Read CSV file
df = pd.read_csv("O3asDataSources.csv")

model_prev = ''
for index, row in df.iterrows():
    # build model name based on source and model
    model = row['source'] + '_' + row['model']
    # construct the model path
    m_path = os.path.join(O3AS_DATA_BASEPATH, model)
    if (os.path.isdir(m_path)):
        m_files = os.listdir(m_path)
        # if the metadata.yaml exists, load it. Otherwise create meta dict
        if "metadata.yaml" in m_files:
            with open(os.path.join(m_path, "metadata.yaml"), "r") as stream:
                meta = yaml.safe_load(stream)
        else:
            meta = {'model' : model,
                     TCO3: {
                          "isdata": False,
                          "plotstyle": {
                              'color': "black",
                              'linestyle': "solid"
                              }
                          },
                     TCO3Return: {
                          "isdata": False,
                          "plotstyle": {
                              'color': "black",
                              'linestyle': "solid"
                              }
                          },
                     VMRO3: {
                          "isdata": False,
                          "plotstyle": {
                              'color': "black",
                              'linestyle': "solid"
                              }
                          },
                   }

        # set colors with the values from GoogleSheet
        meta[row['parameter']]['plotstyle'] = {
                                          'color': row['plot_color'],
                                          'linestyle': row['plot_linestyle'],
                                          'marker': row['plot_marker']
                                         }

        if model is not model_prev:
            # model 1st entry => colors for all plot types set the same
            for ptype in PLOT_TYPES:
                meta[ptype]['plotstyle'].update(meta[row['parameter']]['plotstyle'])
            # check for the data in directory, if there => isdata=True
            for f in os.listdir(m_path):
                 if "tco3" in f:
                     meta[TCO3]['isdata'] = True
                     meta[TCO3Return]['isdata'] = True
                 if "vmro3" in f:
                     meta[VMRO3]['isdata'] = True

        # finally save the meta in metadata.yaml
        metadata_path = os.path.join(m_path, 'metadata.yaml')
        with open(metadata_path, 'w+') as outfile:
            yaml.dump(meta, outfile, default_flow_style=False)
        meta_yaml = yaml.dump(meta, default_flow_style=False)
        print("{}:\n{}".format(model, meta_yaml)) if debug else ''
        model_prev = model
