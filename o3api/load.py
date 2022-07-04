#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 - 2022 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

"""
Module containing the LoadData class to initialize datasets and load them in-memory
"""

import glob
import o3api.config as cfg
import os
import logging
import xarray as xr

import cProfile
import io
import pstats
from functools import wraps

# to check size of data in the memory
# https://github.com/pympler/pympler
#from pympler import asizeof

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

logger = logging.getLogger('__name__') #__name__ #o3api
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
logger.setLevel(logging.INFO)


def _profile(func):
    """Decorate function for profiling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        retval = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative' #SortKey.CUMULATIVE  # 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return wrapper

class LoadData:
    """Base Class to initialize the dataset

    :param plot_type: The plot type (e.g. tco3_zm, tco3_return, vmro3_zm, ...)
    """

    def __init__ (self, data_basepath, plot_type):
        """Constructor method
        """
        self.data_basepath = data_basepath
        self.plot_type = plot_type
        self._data_pattern = self.plot_type + "*.nc"
        # tco3_return uses the same data as tco3_zm :
        if plot_type == "tco3_return":
            self._data_pattern = "tco3*.nc"
        self._datafile_paths = [] #None

    def __set_datafile_paths(self):
        """Set the list of datafile paths corresponding to 
           the O3 plot type (self._datafile_paths).
           Scans all directories in the O3AS_DATA_BASEPATH.
        """

        self._datafile_paths = glob.glob(os.path.join(self.data_basepath,
                                                      '**', 
                                                      self._data_pattern))
        self._datafile_paths.sort()

    def load_dataset(self, model_path):
        """Load dataset from the datafile path (one model)

        :param model_path: Full path to the model data
        :return: xarray Dataset with the model data
        :rtype: xarray.Dataset
        """
        ds = xr.open_dataset(model_path, 
                             cache=True,  # True
                             decode_cf=False) # decode_cf=False #faster?
        ds = xr.decode_cf(ds)
        # we are using monthly data, with the 'middle' date,
        # in this case converting with align_on='date' will not miss dates
        # see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.convert_calendar.html
        ds = ds.convert_calendar('standard', TIME, align_on='date', use_cftime=False)

        return ds
    
    def load_dataset_ensemble(self):
        """Load data from the list of datafiles (self._datafile_paths) in memory.

        :return: dictionary of datasets as {'model': xarray dataset }
        """

        self.__set_datafile_paths()
        logger.debug(F"get_dataset_ensemble (total: {len(self._datafile_paths)}): \
                       {self._datafile_paths}")

        # dictionary to hold all data as {'model': dataset}
        ds_ensemble = {}
        
        for mp in self._datafile_paths:
            # find the name of dataset (directory name)
            model = os.path.dirname(mp).split("/")[-1]
            # build up the dictionary of corresponding datasets
            ds_ensemble[model] = self.load_dataset(mp)
            # immediately load it in memory
            ds_ensemble[model].load()
            
        print(F"Loaded {len(ds_ensemble)} {self.plot_type} (zonal mean) models")

        return ds_ensemble


# initialize an empty dictionary
#data = {}
#tco3_zm = LoadDataset("tco3_zm")
#data["tco3_zm"] = tco3_zm.load_dataset_ensemble()
#vmro3_zm = LoadDataset("vmro3_zm")
#data["vmro3_zm"] = vmro3_zm.load_dataset_ensemble()

#print("Memory, tco3_zm:", asizeof.asizeof(data["tco3_zm"]))
#print(F"Loaded {len(data['tco3_zm'])} TCO3 (zonal mean) models")

#print("Memory, vmro3_zm:", asizeof.asizeof(data["vmro3_zm"]))
#print(F"Loaded {len(data['vmro3_zm'])} VMRO3 (zonal mean) models")

#print(data["tco3_zm"]["CCMI-1_ACCESS_ACCESS-CCM-refC2"])
#print(data["tco3_zm"]["SBUV_GSFC_merged-SAT-ozone"])
#print(data["vmro3_zm"])