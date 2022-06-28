# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under its License. Please, see the LICENSE file

# Load metadata from datasources (csv)
# Needed:
#  * Directory with skimmed data (cfg.O3AS_DATA_BASEPATH)
#  * CSV file exported from the GoogleSheet "Data sources" (cfg.O3AS_DATA_SOURCES_CSV)
#

import logging
import o3api.config as cfg
import pandas as pd


# Logger configuration
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
#logger.setLevel(logging.DEBUG)

# Directory for Skimmed data
logger.debug(F"Data basepath as {cfg.O3AS_DATA_BASEPATH}")
# File for Data Sources (csv)
logger.info(F"Data Sources file: {cfg.O3AS_DATA_SOURCES_CSV}")

# Plot types
TCO3 = cfg.netCDF_conf['tco3']
TCO3Return = cfg.netCDF_conf['tco3_r']
VMRO3 = cfg.netCDF_conf['vmro3']

# configuration for plotting
plot_c = cfg.plot_conf
PLOT_ST = cfg.plot_conf['plot_st']

# Read CSV file
df = pd.read_csv(cfg.O3AS_DATA_SOURCES_CSV)

o3metadata = dict()

for index, row in df.iterrows():
    # build model name based on source and model
    model = F"{row['source']}_{row['model']}"
    # set colors with the values from GoogleSheet
    # first re-instantiate meta dictionary (otherwise would need copy.deepcopy())
    # NB: about copying of dictionaries, see:
    # https://stackoverflow.com/questions/2465921/how-to-copy-a-dictionary-and-only-edit-the-copy
    defaults = {
                TCO3: {
                     PLOT_ST: {"color": "black", "linestyle": "solid"},
                },
                TCO3Return: {
                    PLOT_ST: {"color": "black", "linestyle": "solid"},
                },
                VMRO3: {
                    PLOT_ST: {"color": "black", "linestyle": "solid"},
                }
    }
    # get either defaults or an entry from metadata
    # (Remember: one dataframe row per plot type)
    meta = o3metadata.get(model, defaults)
    # update meta for the plot type with values from GoogleSheet 
    meta[row["parameter"]][PLOT_ST] = {
        key.replace("plot_", ""): value for key, value in row.items() if "plot_" in key
    }

    # use same style for TCO3 and TCO3Return
    if row["parameter"] == TCO3:
        meta[TCO3Return][PLOT_ST] = meta[TCO3][PLOT_ST]

    # finally save the meta into the metadata variable
    o3metadata.update({model: meta})

logger.debug(F"[loadmeta]: {o3metadata}")
