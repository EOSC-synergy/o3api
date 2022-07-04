# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 - 2022 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

"""
Module with help functions to create figures
"""

import o3api.config as cfg
import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# conigure python logger
logger = logging.getLogger('__name__') #o3api
logger.setLevel(cfg.log_level)

# configuration for netCDF
TIME = cfg.netCDF_conf['t_c']
LAT = cfg.netCDF_conf['lat_c']

# configuration for API
PTYPE = cfg.api_conf['plot_t']
MODELS = cfg.api_conf['models']
BEGIN = cfg.api_conf['begin']
END = cfg.api_conf['end']
MONTH = cfg.api_conf['month']
LAT_MIN = cfg.api_conf['lat_min']
LAT_MAX = cfg.api_conf['lat_max']

# configuration for plotting
plot_c = cfg.plot_conf

def cleanse_models(**kwargs):
    """Cleansing models from empty entries, spaces, and quotes

    :param kwargs: The provided in the API call parameters
    :return: models cleansed from empty entries, spaces, quotes
    :rtype: list
    """

    model_kwargs = list(filter(None, kwargs[MODELS])) # remove empty elements
    # strip possible spaces in front and back, and then quotas
    models = [ m.strip().strip('\"') for m in model_kwargs ]
    
    return models

def get_date_range(ds):
    """Return the range of dates in the provided dataset

    :param ds: xarray dataset to check
    :return: date_min, date_max
    """
    date_min = np.amin(ds.coords[TIME].values)
    date_max = np.amax(ds.coords[TIME].values)

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


def get_plot_params(**kwargs):
    """Get plot parameters

    :param kwargs: The provided in the API call parameters
    :return: plot_params with added input parameters
    :rtype: string
    """
    plot_type = kwargs[PTYPE]
    plot_params = ("requested: " + plot_type + ", " + 
                  str(kwargs[BEGIN]) + ".." + str(kwargs[END]))
    if len(kwargs[MONTH]) > 0:
        plot_params += (", month: ")
        for i in kwargs[MONTH]:
            plot_params += str(i) + "," 
        #plot_params = plot_params[:-1] + ""
    else:
        plot_params += ", full_year,"

    deg_sign= u'\N{DEGREE SIGN}'
    plot_params += (" latitudes: " + str(kwargs[LAT_MIN]) + deg_sign + ".." +
                   str(kwargs[LAT_MAX]) + deg_sign)

    return plot_params

def get_plot_info_txt(**kwargs):
    """Generate info text for the plot

    :param kwargs: The provided  in the API call parameters
    :return: information text with legal info, parameters etc
    :rtype: string
    """

    params_txt = get_plot_params(**kwargs)
    plot_infotxt=F"""
{cfg.O3AS_LEGALINFO_TXT} \n
{cfg.O3AS_LEGALINFO_URL} \n \n
{cfg.O3AS_ACKNOWLEDGMENT_TXT} \n
{cfg.O3AS_ACKNOWLEDGMENT_URL} \n\n
This plot is generated with {cfg.O3AS_MAIN_URL} \n\n
The following input parameters were used for the plot:\n
{params_txt}
"""
    
    return plot_infotxt

def get_plot_info_html(**kwargs):
    """Generate info text (HTML) for the plot

    :param kwargs: The provided  in the API call parameters
    :return: information text (HTML) with legal info, parameters etc
    :rtype: string
    """

    params_txt = get_plot_params(**kwargs)
    plot_infohtml=F"""
<p><b>{cfg.O3AS_LEGALINFO_TXT}</b></p><br>
<a href=\"{cfg.O3AS_LEGALINFO_URL}\">{cfg.O3AS_LEGALINFO_URL}</a>
<p></p>
<p><b>{cfg.O3AS_ACKNOWLEDGMENT_TXT}</b></p><br>
<a href=\"{cfg.O3AS_ACKNOWLEDGMENT_URL}\">{cfg.O3AS_ACKNOWLEDGMENT_URL}</a>
<p></p>
<p>This plot is generated with <a href=\"{cfg.O3AS_MAIN_URL}\">{cfg.O3AS_MAIN_URL}</a> </p>
<p></p>
<p>The following input parameters were used for the plot: </p><br>
{params_txt}
<p></p>
"""
    
    return plot_infohtml

    
def set_filename(**kwargs):
    """Set file name

    :param kwargs: The provided  in the API call parameters
    :return: file_name with added input parameters (no extension given!)
    :rtype: string
    """

    file_name = ''
    for val in cfg.api_conf.values():
        if val == MONTH and len(kwargs[val]) == 0:
            par_str = 'full_year'
        else:
            par_str = str(kwargs[val])
            
        file_name += par_str + "_" if val != MODELS else ''

    # delete last "_"
    file_name = file_name[:-1] + ''

    return file_name


def set_figure_attr(fig, **kwargs):
    """Configure the figure attributes

    :param fig: Figure instance
    :param kwargs: The provided  in the API call parameters
    :return: none
    """
    plot_type = kwargs[PTYPE]
    models = cleanse_models(**kwargs)

    plt.xlabel(plot_c[plot_type]['xlabel'], fontsize='large')
    plt.ylabel(plot_c[plot_type]['ylabel'], fontsize='large')
    #plt.title(set_plot_title(**kwargs),
    #          fontsize='medium', color='gray')
    num_col = len(models) // 12
    num_col = num_col if (len(models) % 12 == 0) else num_col + 1
    ax = plt.gca() # get axis instance
    ax_pos = ax.get_position() # get the axes position

    plt.legend(loc='upper center', 
               bbox_to_anchor=[0., ax_pos.y0-0.575, 0.99, 0.3],
               ncol=num_col, fancybox=True, fontsize='small',
               borderaxespad=0.)
    fig.text(ax_pos.x0 + ax_pos.width - 0.01,
             ax_pos.y0 + ax_pos.height - 0.01,
             'Generated with ' + cfg.O3AS_MAIN_URL,
             fontsize='medium', color='gray',
             ha='right', va='top', alpha=0.5)
