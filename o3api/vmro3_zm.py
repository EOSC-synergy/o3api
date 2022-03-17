# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

import logging
import numpy as np
import o3api.config as cfg
import o3api.debug as dbg
from o3api.prepare import PrepareData
import pandas as pd


logger = logging.getLogger('__name__') #o3api
logger.setLevel(cfg.log_level)

# configuration for netCDF
TIME = cfg.netCDF_conf['t_c']
LAT = cfg.netCDF_conf['lat_c']
TCO3 = cfg.netCDF_conf['tco3']
VMRO3 = cfg.netCDF_conf['vmro3']
TCO3Return = cfg.netCDF_conf['tco3_r']

# configuration for API
api_c = cfg.api_conf


class ProcessForVMRO3(PrepareData):
    """Subclass of :class:`PrepareData` to calculate vmro3_zm
    """
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

    def get_plot_data(self, model):
        """Process the model to get vmro3_zm data for plotting

        :param model: The model to process for vmro3_zm
        :return: xarray dataset for plotting
        :rtype: xarray        
        """
        # data selection according to time and latitude
        ds_slice = super().get_dataslice(model)
        # currently placeholder. another calculation might be needed
        # 20-10-07 vkoz
        ds_vmro3 = ds_slice[[VMRO3]]
        logger.debug("ds_vmro3: {}".format(ds_vmro3))

        return ds_vmro3.mean(dim=[LAT])
