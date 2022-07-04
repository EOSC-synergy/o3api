#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 - 2022 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

"""
Module with the PreparaData class to perform data selection
"""

import logging
import numpy as np
import o3api.config as cfg
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


class PrepareData():
    """Class to perform data selection, based on :class:`Dataset`.

    :param begin: Year to start data scanning from
    :param end: Year to finish data scanning
    :param month: Month(s) to select, if not a whole year
    :param lat_min: Minimum latitude to define the range (-90..90)
    :param lat_max: Maximum latitude to define the range (-90..90)
    """

    def __init__ (self, data, **kwargs):
        """Constructor method
        """
        self.data = data
        self.plot_type = kwargs[api_c['plot_t']]
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
        ds = self.data[model]
        logger.debug(F"{model}: Dataset is loaded from the storage location")
        
        # check in what order latitude is used, return them correspondently
        lat_a, lat_b = self.__check_latitude_order(ds)

        # select data according to the period and latitude
        # BUG(?) ccmi-umukca-ucam complains about 31-12-year, but 30-12-year works
        # CFTime360day date format has 30 days for every month???
        # {}-01-01T00:00:00 .. {}-12-30T23:59:59
        if len(self.month) > 0:
            if all(x in range(1,13) for x in self.month):
                ds = ds.sel(time=ds.time.dt.month.isin(self.month))
            else:
                logger.warning(F"Wrong month number! Using whole year range.\
                Check values: {self.month}.")

        ds_slice = ds.sel(time=slice(F"{self.begin}-01", 
                                     F"{self.end}-12"),
                          lat=slice(lat_a,
                                    lat_b))  # latitude
        #print("get_dataslice:", model, ds)
        # maybe skip years selection here? performance?
        #ds_slice = ds.sel(lat=slice(lat_a,
        #                            lat_b))  # latitude

        return ds_slice

    def to_pd_dataframe(self, ds, model) -> pd.DataFrame:
        """Convert xarray variable to pandas dataframe (faster method?)
        
        :param ds: xarray dataset
        :param model: The model to process for self.plot_type
        :return: dataset as pandas dataframe
        :rtype: pandas dataframe
        """

        # convert to pandas series to keep date information
        # different time axes should be harmonized in o3skim.. 
        if (type(ds.indexes[TIME]) is 
            pd.core.indexes.datetimes.DatetimeIndex) :
            time_axis = ds.indexes[TIME].values
        else:
            # convert CFTimeIndex to pd.DatetimeIndex, turn Warnings Off (unsafe=True)
            time_axis = ds.indexes[TIME].to_datetimeindex()

        pd_model = pd.DataFrame({ model: np.nan_to_num(ds[self.plot_type]),
                                  'time': time_axis}).replace({0: np.nan})
        # set index to 'time', also important for performance pd.join() (?)
        pd_model = pd_model.set_index('time')

        return pd_model

    def get_raw_data_pd(self, model) -> pd.DataFrame:
        """Process the model to get tco3_zm raw data

        :param model: The model to process for tco3_zm
        :return: raw data points in preparation for plotting
        :rtype: pd.DataFrame
        """
        # data selection according to time and latitude
        ds_slice = self.get_dataslice(model)
        ds_plot_type = ds_slice[[TCO3]].mean(dim=[LAT])
        logger.debug("ds_plot_type: {}".format(ds_plot_type))

        data = self.to_pd_dataframe(ds_plot_type, model)
        return data

    def get_raw_ensemble_pd(self, models) -> pd.DataFrame:
        """Build the ensemble of tco3_zm models

        :param models: Models to process for tco3_zm
        :return: ensemble of models as pd.DataFrame
        :rtype: pd.DataFrame
        """

        data = self.get_raw_data_pd(models[0]) # initialize with first model
        if len(models) > 1:
            ## PERFORMANCE? map() and join should be faster than 'for' and merge
            # how="outer" is important in order to keep all indecies/dates
            data_list = map(self.get_raw_data_pd, models[1:])
            data = data.join(data_list, how="outer")

            ## previous method uses merge
            #for m in models[1:]:
            #   data = data.merge(self.get_raw_data_pd(m), 
            #                     how='outer',
            #                     on=['time'])
            ##

        return data.sort_index()
