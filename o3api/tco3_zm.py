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
from scipy import signal


logger = logging.getLogger('__name__')
logger.setLevel(cfg.log_level)

# configuration for netCDF
TIME = cfg.netCDF_conf['t_c']
LAT = cfg.netCDF_conf['lat_c']
TCO3 = cfg.netCDF_conf['tco3']
VMRO3 = cfg.netCDF_conf['vmro3']
TCO3Return = cfg.netCDF_conf['tco3_r']

# configuration for API
api_c = cfg.api_conf


class ProcessForTCO3Zm(PrepareData):
    """Subclass of :class:`PrepareData` to calculate tco3_zm
    """
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)
        self.ref_meas = kwargs[api_c['ref_meas']]
        self.ref_year = kwargs[api_c['ref_year']]
        self.ref_fillna = kwargs[api_c['ref_fillna']]
        self.ref_value, self.ref_data = self.get_ref_value()

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


    def get_ensemble_yearly(self, models) -> pd.DataFrame:
        """Rebin tco3_zm data for yearly entries:
            (0). optionally interpolate missing values in the reference measurement
            1. group by year
            2. average by applying mean()
        
        :param models: Models to process for tco3 plots
        :return: yearly averaged data points
        :rtype: pd.DataFrame
        """
        data = super().get_raw_ensemble_pd(models)

        # try to interpolate values in the ref_meas
        if self.ref_meas in models and self.ref_fillna:
            data[self.ref_meas] = data[self.ref_meas].interpolate(method='linear',
                                                                  limit_direction='forward',
                                                                  axis=0)
        data = data.groupby([data.index.year], dropna=True).mean()

        # select data according to the years requested
        #return data[(data.index>=self.begin) & (data.index<=self.end)]
        
        return data

    def get_ref_value(self):
        """Get reference value for the reference year
        
        :return: reference value (tco3_zm at reference year)
        """

        # get ref_meas averaged over a year
        ref_data = self.get_ensemble_yearly([self.ref_meas])
        # select ref_year and find ref_value
        ref_value = ref_data[ref_data.index == self.ref_year].iloc[0][self.ref_meas]
        logger.debug("ref_value: {} => {}".format(ref_data, ref_value))

        return ref_value, ref_data

    def get_ensemble_smoothed(self, models, smooth_win) -> pd.DataFrame:
        """Smooth tco3_zm data using boxcar
        
        :param models: Models to process for tco3_return
        :return: smoothed data points
        :rtype: pd.DataFrame
        """        
        data = self.get_ensemble_yearly(models)
        # ToDo: check for a better method. Now works if NaN years < smooth_win
        # if first years have NaNs fill them with "before NaN values"
        first_year = data.index.values[0]
        data[data.index < (first_year + smooth_win)] = data[data.index < (first_year + smooth_win)].fillna(method='bfill')
        # if last years have NaNs fill them with "before NaN values"
        last_year = data.index.values[-1]
        data[data.index > (last_year - smooth_win)] = data[data.index > (last_year - smooth_win)].fillna(method='ffill')
        data = data.apply(self.__smooth_boxcar, 
                                   args = [smooth_win], 
                                   axis = 0,
                                   result_type = 'broadcast'
                                   )
        
        return data

    def get_ensemble_shifted(self, data) -> pd.DataFrame:
        """Shift tco3_zm data to reference year
        
        :param data: data to process as pd.DataFrame
        :return: shifted data points for plotting 
        :rtype: pd.DataFrame
        """

        data_ref_year = data[data.index == self.ref_year].mean()
        shift = self.ref_value - data_ref_year
        data_shift = data + shift.values
        
        return data_shift
        
    def get_ensemble_stats(self, data) -> pd.DataFrame:
        """Calculate Mean, Std, Median for tco3_zm data
        
        :param data: data to process as pd.DataFrame
        :return: updated pd.DateFrame with stats columns 
        :rtype: pd.DataFrame
        """
        # make data copy, as adding a new "Mean" column
        # affects "Median" calculation, issue#52
        data_in = data.copy(deep=True)
        
        # exclude also ref_measurement from the calculation of statistics
        models = data_in.columns.to_list()
        if self.ref_meas in models:
            data_in.drop(self.ref_meas, axis=1, inplace=True)
        
        # calculate stats
        data['MMMean'] = data_in.mean(axis=1, skipna=True)
        data_std = data_in.std(axis=1, skipna=True)
        data['MMMean-Std'] = data['MMMean'] - data_std
        data['MMMean+Std'] = data['MMMean'] + data_std
        data['MMMedian'] = data_in.median(axis=1, skipna=True) 
        
        return data

    #@dbg._profile
    def get_ensemble_for_plot(self, models) -> pd.DataFrame:
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
            data_plot[self.ref_meas] = self.ref_data

        # inject 'reference_value'
        data_plot['reference_value'] = self.ref_value

        return data_plot


class ProcessForTCO3ZmReturn(ProcessForTCO3Zm):
    """Subclass of :class:`ProcessForTCO3Zm` to calculate tco3_return
    """
    def __init__(self, data, **kwargs):
        # to properly retrieve skimmed data, set to TCO3 data
        kwargs[api_c['plot_t']] = TCO3
        super().__init__(data, **kwargs)
        self.region = kwargs['region']
      
    def get_return_years(self, data):
        """Calculate return year for every model
        
        :param data: data to process
        :return: return years for models
        :rtype: pd.DataFrame
        """
        refMargin = cfg.O3AS_TCO3Return_REF_YEAR_MARGIN
        logger.debug(F"{self.ref_year}: {self.ref_value} (ref_value)")
        def __get_return_year(data):
            # 1. search for years with tco3_zm > ref_value
            # 2. remove duplicates
            # 3. only two rows will be left (False, True)
            data_return = (data[data.index>(self.ref_year+refMargin)]>self.ref_value).drop_duplicates()
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
        data = super().get_ensemble_smoothed(models, boxcar_win)
        data_shift = super().get_ensemble_shifted(data)
        data_tco3 = super().get_ensemble_stats(data_shift)
        data_return_years = self.get_return_years(data_tco3)

        return data_return_years