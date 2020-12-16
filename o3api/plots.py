# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

import glob
import matplotlib.pyplot as plt
import numpy as np
import o3api.config as cfg
import o3api.plothelpers as phlp
import os
import logging
import pandas as pd
from scipy import signal
from statsmodels.tsa.seasonal import seasonal_decompose # accurate enough
import xarray as xr

import cProfile
import io
import pstats
from functools import wraps

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
    if plot_type == TCO3:
        data = ProcessForTCO3(**kwargs)
    elif plot_type == VMRO3:
        data = ProcessForVMRO3(**kwargs)
    elif plot_type == TCO3Return:
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
        # strip possible spaces in front and back, and then quotas
        model = model.strip().strip('\"')
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

        if chunk_size > 0:
            ds = xr.open_mfdataset(self._datafiles, 
                                   chunks={LAT: chunk_size },
                                   concat_dim=TIME,
                                   data_vars='minimal', coords='minimal',
                                   parallel=False)
        else:
            ds = xr.open_mfdataset(self._datafiles,
                                   concat_dim=TIME,
                                   data_vars='minimal',
                                   coords='minimal',
                                   parallel=False)
        return ds

    
class DataSelection(Dataset):
    """Class to perform data selection, based on :class:`Dataset`.

    :param begin: Year to start data scanning from
    :param end: Year to finish data scanning
    :param month: Month(s) to select, if not a whole year
    :param lat_min: Minimum latitude to define the range (-90..90)
    :param lat_max: Maximum latitude to define the range (-90..90)
    """

    def __init__ (self, plot_type, **kwargs):
        """Constructor method
        """
        super().__init__(plot_type, **kwargs)
        self.begin = kwargs[api_c['begin']]
        self.end = kwargs[api_c['end']]
        self.month = kwargs[api_c['month']]
        self.lat_min = kwargs[api_c['lat_min']]
        self.lat_max = kwargs[api_c['lat_max']]

    def __check_latitude_order(self, ds):
        """Function to check the latitude order, 
        returns them correctly ordered

        :param ds: xarray dataset to check
        :return: lat_0, lat_last
        """
        # check in what order latitude is used, e.g. (-90..90) or (90..-90)
        lat_0 = np.amin(ds.coords[LAT].values[0]) # min latitude
        lat_last = np.amax(ds.coords[LAT].values[-1]) # max latitude

        if lat_0 < lat_last:
            lat_a = self.lat_min
            lat_b = self.lat_max
        else:
            lat_a = self.lat_max
            lat_b = self.lat_min

        return lat_a, lat_b

        
    def get_dataslice(self, model):
        """Function to select the slice of data according 
        to the time and latitude requested

        :param model: The model to process
        :return: xarray dataset selected according to the time and latitude
        :rtype: xarray
        """
        ds = super().get_dataset(model)
        logger.info("Dataset is loaded from storage location: {}".format(ds))
        
        # check in what order latitude is used, return them correspondently
        lat_a, lat_b = self.__check_latitude_order(ds)

        # select data according to the period and latitude
        # BUG(?) ccmi-umukca-ucam complains about 31-12-year, but 30-12-year works
        # CFTime360day date format has 30 days for every month???
        # {}-01-01T00:00:00 .. {}-12-30T23:59:59
        if len(self.month) > 0:
            ds = ds.sel(time=ds.time.dt.month.isin(self.month))

        ds_slice = ds.sel(time=slice("{}-01".format(self.begin), 
                                     "{}-12".format(self.end)),
                          lat=slice(lat_a,
                                    lat_b))  # latitude
        return ds_slice
        
    def get_1980slice(self, model):
        """Function to select the slice for 1980 (reference year) 
 
        :param model: The model to process
        :return: xarray dataset selected according to the time and latitude
        :rtype: xarray
        """
        ds = super().get_dataset(model)
        # check in what order latitude is used, return them correspondently
        lat_a, lat_b = self.__check_latitude_order(ds)
        if len(self.month) > 0:
            ds = ds.sel(time=ds.time.dt.month.isin(self.month))        
        ds_1980 = ds.sel(time=slice("1980-01", "1980-12"), 
                         lat=slice(lat_a, lat_b))  # latitude
        return ds_1980


class ProcessForTCO3(DataSelection):
    """Subclass of :class:`DataSelection` to calculate tco3_zm
    """
    def __init__(self, **kwargs):
        super().__init__(TCO3, **kwargs)
        
    def __to_pd_series(self, ds, model):
        """Convert xarray to pandas series
        
        :param ds: xarray dataset
        :param model: The model to process for tco3_zm
        :return dataset as pandas series
        :rtype: pandas series
        """

        # convert to pandas series to keep date information
        if (type(ds.indexes[TIME]) is 
            pd.core.indexes.datetimes.DatetimeIndex) :
            time_axis = ds.indexes[TIME].values
        else:
            time_axis = ds.indexes[TIME].to_datetimeindex()

        curve = pd.Series(np.nan_to_num(ds[TCO3]),
                          index=pd.DatetimeIndex(time_axis),
                          name=model)
        return curve

    def get_raw_data(self, model):
        """Process the model to get tco3_zm raw data

        :param model: The model to process for tco3_zm
        :return: raw data points in preparation for plotting
        :rtype: pandas series (pd.Series)        
        """
        # data selection according to time and latitude
        ds_slice = super().get_dataslice(model)
        ds_tco3 = ds_slice[[TCO3]].mean(dim=[LAT])
        logger.debug("ds_tco3: {}".format(ds_tco3))

        data = self.__to_pd_series(ds_tco3, model)

        return data
        
    def get_plot_data(self, model):
        """Plot tco3_zm data applying a smoothing function (boxcar)
        :param model: The model to process for tco3_zm
        :return: ready for plotting data
        :rtype: pandas series (pd.Series)
        """
        
        curve = self.get_raw_data(model)
        time_axis = curve.index
        curve_values = curve.values
        boxcar_win = 3
        boxcar = np.ones(boxcar_win)
        boxcar_values = signal.convolve(curve_values, 
                                        boxcar, 
                                        mode='same')/np.sum(boxcar)
        logger.debug("time_axis.shape = {}, boxcar_values.shape = {}"
                     .format(time_axis.shape, boxcar_values.shape))
        boxcar_values[0] = curve_values[0]
        boxcar_values[-1] = curve_values[-1]
        #boxcar_values[1] = curve_values[1]
        #boxcar_values[-2] = curve_values[-2]
        logger.debug(F"boxcar_values[:5]  : {boxcar_values[:5]}")
        logger.debug(F"vs curve_values[:5]: {curve_values[:5]}")
        logger.debug(F"boxcar_values[-5:]  : {boxcar_values[-5:]}")
        logger.debug(F"vs curve_values[-5:]: {curve_values[-5:]}")
        boxcar_smooth = pd.Series(boxcar_values,
                                  index=time_axis,
                                  name=model)
        return boxcar_smooth

    def get_ref1980(self, model):
        """Process the model to get tco3_zm reference for 1980

        :param model: The model to process for tco3_zm
        :return: xarray dataset for 1980
        :rtype: xarray        
        """
        # data selection according to 1980 and latitude
        ds_slice = super().get_1980slice(model)
        ds_tco3_1980 = ds_slice[[TCO3]].mean(dim=[LAT])
        #logger.debug("ds_tco3_1980: {}".format(ds_tco3_1980.to_dataframe()))
        ref1980 = ds_tco3_1980.to_dataframe().mean().values[0]

        return ref1980


class ProcessForVMRO3(DataSelection):
    """Subclass of :class:`DataSelection` to calculate vmro3_zm
    """
    def __init__(self, **kwargs):
        super().__init__(VMRO3, **kwargs)

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
        

class ProcessForTCO3Return(DataSelection):
    """Subclass of :class:`DataSelection` to calculate tco3_return
    """
    def __init__(self, **kwargs):
        super().__init__(TCO3Return, **kwargs)

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
        ds_tco3_return = ds_slice[[TCO3Return]]
        logger.debug("ds_tco3_return: {}".format(ds_tco3_return))

        return ds_tco3_return.mean(dim=[LAT])
