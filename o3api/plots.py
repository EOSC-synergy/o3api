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


class Dataset:
    """Base Class to initialize the dataset

    :param plot_type: The plot type (e.g. tco3_zm, vmro3_zm, ...)
    """
    def __init__ (self, plot_type, **kwargs):
        """Constructor method
        """
        self.plot_type = plot_type
        self._data_pattern = self.plot_type + "*.nc"
        # tco3_return uses the same data as tco3_zm :
        if plot_type == "tco3_return":
            self._data_pattern = "tco3*.nc"
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
        """Load data from one datafile

        :param model: The model to process
        :return: xarray dataset
        :rtype: xarray.Dataset
        """
        logging.debug(F"get_dataset: {model}")
        self.__set_datafiles(model)
        ds = xr.open_dataset(self._datafiles[0], 
                             cache=True,
                             decode_cf=False) # decode_cf=False #faster?
        ds = xr.decode_cf(ds)
        return ds
        
    def get_mfdataset(self, model):
        """Load data from the datafile list

        :param model: The model to process
        :return: xarray dataset
        :rtype: xarray.Dataset
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
                                   parallel=False) #False
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
        logger.debug(F"{model}: Dataset is loaded from the storage location")
        logger.debug(ds)
        
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

        ds_slice = ds.sel(time=slice("{}-01".format(self.begin), 
                                     "{}-12".format(self.end)),
                          lat=slice(lat_a,
                                    lat_b))  # latitude
        return ds_slice


    def to_pd_series(self, ds, model):
        """Convert xarray variable to pandas series
        
        :param ds: xarray dataset
        :param model: The model to process for self.plot_type
        :return dataset as pandas series
        :rtype: pandas series
        """

        # convert to pandas series to keep date information
        if (type(ds.indexes[TIME]) is 
            pd.core.indexes.datetimes.DatetimeIndex) :
            time_axis = ds.indexes[TIME].values
        else:
            time_axis = ds.indexes[TIME].to_datetimeindex()

        curve = pd.Series(np.nan_to_num(ds[self.plot_type]),
                          index=pd.DatetimeIndex(time_axis),
                          name=model).replace({0: np.nan})
        return curve


    def to_pd_dataframe(self, ds, model):
        """Convert xarray variable to pandas dataframe (faster method?)
        
        :param ds: xarray dataset
        :param model: The model to process for self.plot_type
        :return dataset as pandas dataframe
        :rtype: pandas dataframe
        """

        # convert to pandas series to keep date information
        if (type(ds.indexes[TIME]) is 
            pd.core.indexes.datetimes.DatetimeIndex) :
            time_axis = ds.indexes[TIME].values
        else:
            time_axis = ds.indexes[TIME].to_datetimeindex()

        pd_model = pd.DataFrame({ model: np.nan_to_num(ds[self.plot_type]),
                                  'time': time_axis}).replace({0: np.nan})
        pd_model = pd_model.set_index('time')
        return pd_model


class ProcessForTCO3(DataSelection):
    """Subclass of :class:`DataSelection` to calculate tco3_zm
    """
    def __init__(self, **kwargs):
        super().__init__(TCO3, **kwargs)
        self.ref_meas = kwargs[api_c['ref_meas']]
        self.ref_year = kwargs[api_c['ref_year']]

    def __smooth_boxcar(self, data, bwindow):
        """Function to apply boxcar, following
        https://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
        N.B. 'valid' replaced with 'same' !
        """        
        boxcar = np.ones(bwindow)
        logger.debug("signal(raw) (len={}): {}".format(len(data),data))
        # may have a problem with NaNs. try to interpolate. somehow does not work... comment.
        # https://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array?noredirect=1&lq=1
        #nans, x= np.isnan(data), lambda z: z.nonzero()[0]
        #data[nans]= np.interp(x(nans), x(~nans), data[~nans])
        # mirror start and end of the original signal:
        sgnl = np.r_[data[bwindow-1:0:-1],data,data[-2:-bwindow-1:-1]]
        logger.debug("Signal (len={}): {}".format(len(sgnl),sgnl))
        boxcar_values = signal.convolve(sgnl,
                                        boxcar, 
                                        mode='same')/bwindow
        logger.debug("Signal+boxcar (len={}): {}".format(len(boxcar_values), 
                                            boxcar_values))
        return boxcar_values[bwindow-1:-(bwindow-1)]
        
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

        data = self.to_pd_series(ds_tco3, model)

        return data

    def get_raw_data_pd(self, model):
        """Process the model to get tco3_zm raw data

        :param model: The model to process for tco3_zm
        :return: raw data points in preparation for plotting
        :rtype: pd.DataFrame
        """
        # data selection according to time and latitude
        ds_slice = super().get_dataslice(model)
        ds_tco3 = ds_slice[[TCO3]].mean(dim=[LAT])
        logger.debug("ds_tco3: {}".format(ds_tco3))

        data = self.to_pd_dataframe(ds_tco3, model)
        return data
    
    def get_raw_ensemble_pd(self, models):
        """Build the ensemble of tco3_zm models

        :param models: Models to process for tco3_zm
        :return: ensemble of models as pd.DataFrame
        :rtype: pd.DataFrame
        """        

        data = self.get_raw_data_pd(models[0]) # initialize with first model
        for m in models[1:]:
            data = data.merge(self.get_raw_data_pd(m), 
                             how='outer',
                             on=['time'],
                             sort=True)

        pd.options.display.max_columns = None
        return data

    def get_ensemble_yearly(self, models):
        """Rebin tco3_zm data for yearly entries
        
        :param models: Models to process for tco3_return
        :return: yearly data points
        :rtype: pd.DataFrame
        """
        data = self.get_raw_ensemble_pd(models)
        return data.groupby([data.index.year]).mean()

    def get_ref_value(self):
        """Get reference value for the reference year
        
        :return: reference value (tco3_zm at reference year)
        """
        ref_data = self.get_raw_data_pd(self.ref_meas)
        ref_values = ref_data[self.ref_meas][ref_data.index.year == self.ref_year].interpolate(method='linear').values
        ref_value = np.mean(ref_values)
        return ref_value

    def get_ensemble_smoothed(self, models, smooth_win):
        """Smooth tco3_zm data using boxcar
        
        :param models: Models to process for tco3_return
        :return: smoothed data points
        :rtype: pd.DataFrame
        """        
        data = self.get_ensemble_yearly(models)
        last_year = data.index.values[-1]
        # if last years have NaNs fill them with "before NaN values"
        data[data.index > (last_year - smooth_win)] = data[data.index > (last_year - smooth_win)].fillna(method='ffill')
        data = data.apply(self.__smooth_boxcar, args = [smooth_win], axis = 0, result_type = 'broadcast')
        
        return data

    def get_ensemble_shifted(self, data):
        """Shift tco3_zm data to reference year
        
        :param data: data to process as pd.DataFrame
        :return: shifted data points for plotting 
        :rtype: pd.DataFrame
        """

        ref_value = self.get_ref_value()
        data_ref_year = data[data.index == self.ref_year].mean()
        shift = ref_value - data_ref_year
        data_shift = data + shift.values
        
        return data_shift
        
    def get_ensemble_stats(self, data):
        """Calculate Mean, Std, Median for tco3_zm data
        
        :param data: data to process as pd.DataFrame
        :return: updated pd.DateFrame with stats columns 
        :rtype: pd.DataFrame
        """        
        data['MMMean'] = data.mean(axis=1, skipna=True)
        data_std = data.std(axis=1, skipna=True)
        data['MMMean-Std'] = data['MMMean'] - data_std
        data['MMMean+Std'] = data['MMMean'] + data_std
        data['MMMedian'] = data.median(axis=1, skipna=True) 
        
        return data

    def get_ensemble_for_plot(self, models):
        """Build the ensemble of tco3_zm models for plotting, include reference

        :param models: Models to process for tco3_zm
        :return: ensemble of models, including the reference, as pd.DataFrame
        :rtype: pd.DataFrame
        """  
        boxcar_win = cfg.O3AS_TCO3Return_BOXCAR_WINDOW
        data = self.get_ensemble_smoothed(models, boxcar_win)
        data_shift = self.get_ensemble_shifted(data)
        data_plot = self.get_ensemble_stats(data_shift)

        if self.ref_meas in models:
            data_ref_meas = self.get_ensemble_yearly([self.ref_meas])
            data_plot[self.ref_meas] = data_ref_meas[self.ref_meas]

        # inject 'reference_value'
        ref_value = self.get_ref_value()
        #ref_df = pd.DataFrame({'reference_value': [ref_value, ref_value], 
        #                       'time': [data.index[0], 
        #                                data.index[-1]]}).set_index('time')
        #data_plot = data_plot.merge(ref_df, how='outer', on=['time'], sort=True)
        data_plot['reference_value'] = ref_value

        return data_plot

class ProcessForTCO3Return(ProcessForTCO3):
    """Subclass of :class:`ProcessForTCO3` to calculate tco3_return
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = kwargs['region']
      
    def get_return_years(self, data):
        """Calculate return year for every model
        
        :param data: data to process
        :return: return years for models
        :rtype: pd.DataFrame
        """
        refMargin = 5
        ref_value = self.get_ref_value()
        #logger.debug(F"ref_value: {ref_value}")
        def __get_return_year(data):
            # 1. search for years with tco3_zm > ref_value
            # 2. remove duplicates
            # 3. only two rows will be left (False, True)
            data_return = (data[data.index>(self.ref_year+refMargin)]>ref_value).drop_duplicates()
            try:
                idx = data_return.values.tolist().index(True)
                return_year = data_return.index[idx]
            except:
                return_year = np.nan              

            return return_year

        return_years = {} # model: year
        models = data.columns
        [ return_years.update({m: __get_return_year(data[m])}) for m in models ]
        logger.debug(F"return_years: {return_years}")

        data_return_years = pd.DataFrame(return_years, index=[self.region])
        #data_return_years['mean_year'] = data_return_years.mean(axis=1, skipna=True)
       
        return data_return_years

    def get_ensemble_for_plot(self, models):
        """Build the ensemble of tco3_return points for plotting

        :param models: Models to process for tco3_zm
        :return: ensemble of models, including the mean, as pd.DataFrame
        :rtype: pd.DataFrame
        """  

        boxcar_win = cfg.O3AS_TCO3Return_BOXCAR_WINDOW
        data = self.get_ensemble_smoothed(models, boxcar_win)
        data_shift = self.get_ensemble_shifted(data)
        data_tco3 = self.get_ensemble_stats(data_shift)
        data_return_years = self.get_return_years(data_tco3)

        return data_return_years


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
