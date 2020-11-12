# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

import o3as.config as cfg
import logging
import numpy as np

# conigure python logger
logger = logging.getLogger('__name__') #o3asplot
logger.setLevel(cfg.log_level)

pconf = cfg.plot_conf


def get_date_range(ds):
    """Return the range of dates in the provided dataset

    :param ds: xarray dataset to check
    :return: date_min, date_max
    """
    date_min = np.amin(ds.coords[pconf['time_c']].values)
    date_max = np.amax(ds.coords[pconf['time_c']].values)

    return date_min, date_max


def get_periodicity(pd_time):
    """Calculate periodicity in the provided data

    :param pd_time: The time period
    :type pd_time: pandas DatetimeIndex
    :return: Calculated periodicity as the number of points per year
    :rtype: int
    """
    date_range = np.amax(pd_time) - np.amin(pd_time)
    date_range = (date_range/np.timedelta64(1, 'D'))
    periodicity = ((pd_time.size - 1) / date_range ) * 365.0
    logger.debug("Periodicity calculated: {}".format(periodicity))

    return int(round(periodicity, 0))


def set_plot_title(**kwargs):
    """Set plot title

    :param kwargs: The provided in the API call parameters
    :return: plot_title with added input parameters
    :rtype: string
    """
    plot_type = kwargs[pconf['plot_t']]
    plot_title = plot_type + " (inputs: "
    for par in pconf[plot_type]['inputs']:
        plot_title += str(kwargs[par]) + ","

    plot_title = plot_title[:-1] + ")" # replace last "," with ")"
    
    return plot_title

    
def set_filename(**kwargs):
    """Set file name

    :param kwargs: The provided  in the API call parameters
    :return: file_name with added input parameters (no extension given!)
    :rtype: string
    """
    plot_type = kwargs[pconf['plot_t']]
    file_name = plot_type
    for par in pconf[plot_type]['inputs']:
        file_name += "_" + str(kwargs[par])

    return file_name
