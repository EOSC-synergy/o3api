# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

import glob
import numpy as np
import o3api.config as cfg
import os
import logging
import xarray as xr

import cProfile
import io
import pstats
from functools import wraps

logger = logging.getLogger('__name__') #o3api
logger.setLevel(cfg.log_level)

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

def set_data_processing(plot_type, **kwargs):
    """Function to inizialize proper class for data processing

    :param plot_type: The plot type (e.g. tco3_zm, vmro3_zm, ...)
    :return: object corresponding to the plot type
    """
    if plot_type == 'tco3_zm':
        data = ProcessForTCO3(**kwargs)
    elif plot_type == 'vmro3_zm':
        data = ProcessForVMRO3(**kwargs)
    elif plot_type == 'tco3_return':
        data = ProcessForTCO3Return(**kwargs)
        
    return data


class Dataset:
    """Base Class to initialize the dataset

    :param plot_type: The plot type (e.g. tco3_zm, vmro3_zm, ...)
    """
    def __init__ (self, plot_type, **kwargs):
        """Constructor method
        """
        self.plot_type = plot_type
        self._data_pattern = self.plot_type + "*.nc"
        self._datafiles = [] #None

    def __set_datafiles(self, model):
        """Set the list of corresponding datafiles

        :param model: The model to process
        """        
        self._datafiles = glob.glob(os.path.join(cfg.O3AS_DATA_BASEPATH, 
                                                 model, 
                                                 self._data_pattern))

    def get_dataset(self, model):
        """Load data from the datafile list

        :param model: The model to process
        :return: xarray dataset
        :rtype: xarray
        """
        # Check: http://xarray.pydata.org/en/stable/dask.html#chunking-and-performance
        # chunks={'latitude': 8} - very machine dependent!
        # laptop (RAM 8GB) : 8, lsdf-gpu (128GB) : 64
        # engine='h5netcdf' : need h5netcdf files? yes, but didn't see improve
        # parallel=True : in theory should use dask.delayed 
        #                 to open and preprocess in parallel. Default is False
        self.__set_datafiles(model)
        chunk_size = int(os.getenv('O3API_CHUNK_SIZE', -1))
        logger.debug("Chunk Size: {}".format(chunk_size))

        if chunk_size > 0:
            ds = xr.open_mfdataset(self._datafiles, chunks={'lat': chunk_size },
                                   concat_dim='time',
                                   data_vars='minimal', coords='minimal',
                                   parallel=False)
        else:
            ds = xr.open_mfdataset(self._datafiles,
                                   concat_dim='time',
                                   data_vars='minimal', 
                                   coords='minimal',
                                   parallel=False)
        return ds

    
class DataSelection(Dataset):
    """Class to perform data selection, based on :class:`Dataset`.

    :param b_year: Year to start data scanning from
    :param e_year: Year to finish data scanning
    :param lat_min: Minimum latitude to define the range (-90..90)
    :param lat_max: Maximum latitude to define the range (-90..90)
    """

    def __init__ (self, plot_type, **kwargs):
        """Constructor method
        """
        super().__init__(plot_type, **kwargs)
        self.b_year = kwargs['begin_year']
        self.e_year = kwargs['end_year']
        self.lat_min = kwargs['lat_min']
        self.lat_max = kwargs['lat_max']

    def __check_latitude_order(self, ds):
        """Function to check the latitude order

        :param ds: xarray dataset to check
        :return: lat_0, lat_last
        """
        lat_0 = np.amin(ds.coords['lat'].values[0]) # min latitude
        lat_last = np.amax(ds.coords['lat'].values[-1]) # max latitude

        return lat_0, lat_last

        
    def get_dataslice(self, model):
        """Function to select the slice of data according 
        to the time and latitude requested

        :param model: The model to process
        :return: xarray dataset selected according to the time and latitude
        :rtype: xarray
        """
        ds = super().get_dataset(model)
        logger.info("Dataset is loaded from storage location: {}".format(ds))
        # check in what order latitude is used, e.g. (-90..90) or (90..-90)
        lat_0, lat_last = self.__check_latitude_order(ds)
        logger.debug("ds: lat_0 = {}, lat_last: {}".format(lat_0, lat_last))
        if lat_0 < lat_last:
            lat_a = self.lat_min
            lat_b = self.lat_max
        else:
            lat_a = self.lat_max
            lat_b = self.lat_min

        # select data according to the period and latitude
        # BUG(?) ccmi-umukca-ucam complains about 31-12-year, but 30-12-year works
        # CFTime360day date format has 30 days for every month???
        ds_slice = ds.sel(time=slice("{}-01-01T00:00:00".format(self.b_year), 
                                     "{}-12-30T23:59:59".format(self.e_year)),
                          lat=slice(lat_a,
                                    lat_b))  # latitude
                                     
        return ds_slice


class ProcessForTCO3(DataSelection):
    """Subclass of :class:`DataSelection` to calculate tco3_zm
    """
    def __init__(self, **kwargs):
        super().__init__('tco3_zm', **kwargs)

    def get_plot_data(self, model):
        """Process the model to get tco3_zm data for plotting

        :param model: The model to process for tco3_zm
        :return: xarray dataset for plotting
        :rtype: xarray        
        """
        # data selection according to time and latitude
        ds_slice = super().get_dataslice(model)
        ds_tco3 = ds_slice[["tco3_zm"]]
        logger.debug("ds_tco3: {}".format(ds_tco3))

        return ds_tco3.mean(dim=['lat'])


class ProcessForVMRO3(DataSelection):
    """Subclass of :class:`DataSelection` to calculate vmro3_zm
    """
    def __init__(self, **kwargs):
        super().__init__('vmro3_zm', **kwargs)

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
        ds_vmro3 = ds_slice[["vmro3_zm"]]
        logger.debug("ds_vmro3: {}".format(ds_vmro3))

        return ds_vmro3.mean(dim=['lat'])
        

class ProcessForTCO3Return(DataSelection):
    """Subclass of :class:`DataSelection` to calculate tco3_return
    """
    def __init__(self, **kwargs):
        super().__init__('tco3_return', **kwargs)

    def get_plot_data(self, model):
        """Process the model to get tco3_return data for plotting

        :param model: The model to process for tco3_return
        :return: xarray dataset for plotting
        :rtype: xarray        
        """
        # data selection according to time and latitude
        ds_slice = super().get_dataslice(model)
        # currently placeholder. another calculation might be needed
        # 20-10-07 vkoz
        ds_tco3_return = ds_slice[["tco3_return"]]
        logger.debug("ds_tco3_return: {}".format(ds_tco3_return))

        return ds_tco3_return.mean(dim=['lat'])
