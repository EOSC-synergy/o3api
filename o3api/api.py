#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov
#
# Script to process selected data and 
# return either PDF plot or JSON document.
# Used to build REST API.
#
## Ozone related information: ##
# time: index for time (e.g. hours since start time - 6 hourly spacing)
# lat: latitude index for geolocation
# level: index for pressure / altitude (e.g. hPa)
# t: temperature
# o3: ozone data
# tco3_zm: total column ozone, zonal mean
# ...

# ToDo: improve Error handling, that Errors are correctly returned by API
#       e.g. raise OSError("no files to open")


import o3api.config as cfg
import o3api.plothelpers as phlp
import o3api.plots as o3plots
import json
import logging
import matplotlib.style as mplstyle
mplstyle.use('fast') # faster?
import matplotlib.pyplot as plt
import numpy as np

import os
import pkg_resources
import pandas as pd
import re
import time
import yaml
# try to loader faster CLoader, if not fall into standard Loader
try:
    from yaml import CLoader as Loader, CSafeLoader as SafeLoader, CDumper as Dumper
except ImportError:
    from yaml import Loader, SafeLoader, Dumper

import cProfile
import io
import pstats

from flask import send_file
from flask import jsonify, make_response, request
from fpdf import FPDF
from functools import wraps
from io import BytesIO

# conigure python logger
logger = logging.getLogger('__name__') #o3api
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
logger.setLevel(cfg.log_level)

## Authorization
from flaat import Flaat
flaat = Flaat()

# list of trusted OIDC providers
flaat.set_trusted_OP_list(cfg.trusted_OP_list)

# configuration for API
PTYPE = cfg.api_conf['plot_t']
MODELS = cfg.api_conf['models']
BEGIN = cfg.api_conf['begin']
END = cfg.api_conf['end']
MONTH = cfg.api_conf['month']
LAT_MIN = cfg.api_conf['lat_min']
LAT_MAX = cfg.api_conf['lat_max']
REF_MEAS = cfg.api_conf['ref_meas']
REF_YEAR = cfg.api_conf['ref_year']

TCO3 = cfg.netCDF_conf['tco3']
TCO3Return = cfg.netCDF_conf['tco3_r']
VMRO3 = cfg.netCDF_conf['vmro3']

# configuration for plotting
plot_c = cfg.plot_conf
PLOT_ST = cfg.plot_conf['plot_st']

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

def _catch_error(f):
    """Decorate function to return an error, in case
    """
    # In general, API should return what is requested, i.e.
    # JSON -> JSON, PDF->PDF
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            e_message = []
            e_message.append({ 'status': 'Error',
                               'object': str(type(e)),
                               'message': '{}'.format(e)
                             })
            logger.debug(e_message)
            #raise BadRequest(e)

            if request.headers['Accept'] == "application/pdf":
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size = 14)
                for key, value in e_message[0].items():
                    pdf.write(18, txt = "{} : {}".format(key, value))
                    pdf.ln()
                
                pdf_byte_str = pdf.output(dest='S').encode('latin-1')
                buffer_resp = BytesIO(bytes(pdf_byte_str))
                buffer_resp.seek(0)

                response = make_response(send_file(buffer_resp,
                                         as_attachment=True,
                                         attachment_filename='Error.pdf',
                                         mimetype='application/pdf'), 500)
            else:
                response = make_response(jsonify(e_message), 500)
              
            logger.debug("Response: {}".format(dict(response.headers)))
            return response

    return wrap


def _timeit(func):
    """Measure time of the function
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        time_model = time.time()
        f = func(*args, **kwargs)
        time_described = time.time()
        logger.info("[TIME] One model processed: {}".format(time_described - 
                                                             time_model))
        return f
    return wrap


def __convert_plot_style(models_style, ptype):
    """Function to convert array of dictionaries with model:name to 
       dictionary with named by model elements

       Example:
       [{
         model: name,
         plotstyle: {}
        },
        ...
       ]
        
       to
        
       { name: {},
         ...
       }
       
       :param models_style: input array of dictionaries
       :return: dictionary
    """
    ckwargs = {}
    for mi in models_style:
        model = mi['model']
        ckwargs[model] = {}
        for k,v in mi[ptype][PLOT_ST].items():
            par = k
            if k in plot_c[ptype][PLOT_ST].keys():
                par = plot_c[ptype][PLOT_ST][k]
            ckwargs[model][par] = v
   
    return ckwargs


def __return_json(df, model, pfmt):
    """Function to return JSON

    :param df: data (pandas.DataFrame) to process
    :param model: model to process
    :param pfmt: plot format (e.g. linecolor, marker)
    :return: JSON with points (x,y)
    """
    logger.debug(F"plotstyle: {pfmt}")
    data = {'model': model,
            'x': df[model].dropna().index.tolist(),
            'y': df[model].dropna().values.tolist(), #curve[model]
            PLOT_ST: pfmt
           }
    return data  


@_catch_error
def get_api_info():
    """Return information about the package

    :return: The o3api package info
    :rtype: dict
    """
    module = __name__.split('.', 1)
    pkg = pkg_resources.get_distribution(module[0])
    meta = {
        'name' : None,
        'version' : None,
        'summary' : None,
        'home-page' : None,
        'author' : None,
        'author-email' : None,
        'license' : None
    }
    iline = 0
    top_lines = 10 # take only top 10 lines (otherwise may pick from content)
    for line in pkg.get_metadata_lines("PKG-INFO"):
        line_low = line.lower() # to avoid inconsistency due to letter cases
        if iline < top_lines:
            for par in meta:
                if line_low.startswith(par.lower() + ":", 0):
                    _, value = line.split(": ", 1)
                    meta[par] = value
        iline += 1
    
    logger.debug(F"Found metadata: {meta}")
    return meta


@_catch_error
def get_data_types():
    """Get list of plot types with available data"""

    ptypes = []
    possible_types = [TCO3, TCO3Return, VMRO3]

    kwargs = {}
    for t in possible_types:
        kwargs[PTYPE] = t
        models = get_models_list(**kwargs)
        isdata = True if len(models) > 0 else False    
        ptypes.append(t) if isdata else ''

    return ptypes


@_catch_error
def get_data_tco3_zm(*args, **kwargs):
    """Retrieve data to produce tco3_zm plot

    :param kwargs: provided in the API call parameters
    :return: JSON document with data points
    """
    kwargs[PTYPE] = TCO3
    kwargs[REF_MEAS] = cfg.O3AS_TCO3_REF_MEAS
    kwargs[REF_YEAR] = cfg.O3AS_TCO3_REF_YEAR
    kwargs[MODELS] = phlp.cleanse_models(**kwargs)
    models = kwargs[MODELS]
  
    data = o3plots.ProcessForTCO3(**kwargs)
    tco3_data = data.get_raw_ensemble_pd(models)

    models_style = get_plot_style(**kwargs)
    ckwargs = __convert_plot_style(models_style, TCO3)

    json_output = []
    __json_append = json_output.append

    [ __json_append(__return_json(tco3_data, m, ckwargs[m])) for m in models ]
        
    response = json_output

    return response


@_catch_error
def get_data_tco3_return(*args, **kwargs):
    """Retrieve data to produce tco3_return plot

    :param kwargs: provided in the API call parameters
    :return: JSON document with data points
    """
    kwargs[PTYPE] = TCO3Return
    kwargs[REF_MEAS] = cfg.O3AS_TCO3_REF_MEAS
    kwargs[REF_YEAR] = cfg.O3AS_TCO3_REF_YEAR
    kwargs[MODELS] = phlp.cleanse_models(**kwargs)
    models = kwargs[MODELS]
  
    data = o3plots.ProcessForTCO3(**kwargs)
    tco3_data = data.get_raw_ensemble_pd(models)

    models_style = get_plot_style(**kwargs)
    ckwargs = __convert_plot_style(models_style, TCO3Return)

    json_output = []
    __json_append = json_output.append

    [ __json_append(__return_json(tco3_data, m, ckwargs[m])) for m in models ]
        
    response = json_output

    return response


def get_data_vmro3_zm(*args, **kwargs):
    """Retrieve data to produce vmro3_zm plot

    :param kwargs: provided in the API call parameters
    :return: JSON document with data points
    """
    pass

@_catch_error
def get_models_info():
    """Return dictionary of available models with the meta info
    
    :return: The dictionary of available models
    :rtype: dict
    """
    models = []
    plot_types = get_plot_types()

    colors = ["black", "gray", "red", "chocolate",
              "orange", "gold", "olive", "green",
              "lime", "lightseagreen", "teal", "deepskyblue",
              "navy", "blue", "purple", "magenta"]
    line_styles = ["solid", "dotted", "dashed", "dashdot"]
    markers = [".", "o", "+", "x", "v", "^", "s", "*", "D"]

    m_counter = 0
    list_dir = os.listdir(cfg.O3AS_DATA_BASEPATH)
    list_dir.sort()
    for mdir in list_dir:
        m_path = os.path.join(cfg.O3AS_DATA_BASEPATH, mdir)
        m_files = os.listdir(m_path)
        if (os.path.isdir(m_path)) and any(".nc" in f for f in m_files):
            meta = { 'model' : mdir,
                     TCO3: {
                          "isdata": False,
                          PLOT_ST: {
                              'color': '',
                              'marker': '',
                              'linestyle': ''
                              }
                          },
                     TCO3Return: {
                          "isdata": False,
                          PLOT_ST: {
                              'color': '',
                              'marker': '',
                              'linestyle': ''
                              }
                          },
                     VMRO3: {
                          "isdata": False,
                          PLOT_ST: {
                              'color': '',
                              'marker':'',
                              'linestyle': ''
                              }
                          },
                   }

            # inizialize with some colors
            for pt in plot_types:
                i_color = m_counter % len(colors)
                meta[pt][PLOT_ST]["color"] = colors[i_color]
                i_marker = m_counter % len(markers)
                meta[pt][PLOT_ST]["marker"] = markers[i_marker]
                i_style = m_counter % len(line_styles)
                meta[pt][PLOT_ST]["linestyle"] = line_styles[i_style]

            # update with the info from metadata.yaml's
            if "metadata.yaml" in m_files:
                # update meta from metadata.yaml, if available:
                with open(os.path.join(m_path, "metadata.yaml"), "r") as stream:
                    meta_yaml = yaml.load(stream, Loader=SafeLoader)

                # if plot info is in meta_yaml, update it in meta
                for pt in plot_types:
                    if PLOT_ST in meta_yaml[pt].keys():
                        meta[pt][PLOT_ST].update(meta_yaml[pt][PLOT_ST])
                # if colors are defined for TCO3 and not others, use the same
                if PLOT_ST in meta_yaml[TCO3].keys():
                    if PLOT_ST not in meta_yaml[TCO3Return].keys():
                        meta[TCO3Return][PLOT_ST].update(meta[TCO3][PLOT_ST])
                    if PLOT_ST not in meta_yaml[VMRO3].keys():
                        meta[VMRO3][PLOT_ST].update(meta[TCO3][PLOT_ST])

            # get model attrs. comment. another endpoint?
            #data = o3plots.Dataset(TCO3, **kwargs)
            #ds = data.get_dataset(mdir)
            #model_info_dict = ds.to_dict(data=False)
            #meta['attrs'] = model_info_dict['attrs']

            for f in os.listdir(m_path):
                if "tco3" in f:
                    meta[TCO3]['isdata'] = True
                    meta[TCO3Return]['isdata'] = True
                if "vmro3" in f:
                    meta[VMRO3]['isdata'] = True
            models.append(meta)
            m_counter += 1

    return models

@_catch_error
def get_models_list(*args, **kwargs):
    """Return the list of available Ozone models

    :return: The list of available models
    :rtype: list
    """
    models_list = []

    models_info = get_models_info()
    if PTYPE in kwargs:
        ptype = kwargs[PTYPE]
        for m in models_info:
            if m[ptype]['isdata']:
                models_list.append(m['model'])
    else:
        models_list = [ m['model'] for m in models_info ]

    if 'select' in kwargs:
        pattern = kwargs['select'].lower()
        models_list = [ m for m in models_list if pattern in m.lower() ]

    models_list.sort()
    return models_list

@_catch_error
def get_plot_style(*args, **kwargs):
    """Returning plot style for selected models and plot type
    """
    models_info = get_models_info()
    plots_format = []

    if MODELS in kwargs:
        models = phlp.cleanse_models(**kwargs)
    else:
        models = [ m['model'] for m in models_info ]
    
    # if "models = []", i.e. empty list, get all available models instead
    if len(models) < 1:
        models = [ m['model'] for m in models_info ]

    if PTYPE in kwargs:
        plot_types = [kwargs[PTYPE]]
    else:
        plot_types = get_data_types()

    for m in models_info:
        pfmt = {}
        if m['model'] in models:
            pfmt['model'] = m['model']
            for pt in plot_types:
                pfmt[pt] = {}
                pfmt[pt][PLOT_ST] = m[pt][PLOT_ST]
            plots_format.append(pfmt)

    return plots_format

@_catch_error
def get_model_detail(*args, **kwargs):
    """Return information about the Ozone model

    :return: Info about the Ozone model
    :rtype: dict
    """
    model = kwargs['model'].lstrip().rstrip()
    models_info = get_models_info()
    model_info_dict = {}
    for m in models_info:
        if m['model'] == model:
            model_info_dict = m

    plot_types = get_data_types()
    for pt in plot_types:
        if model_info_dict[pt]['isdata']:
            # create dataset according to the plot type (tco3_zm, vmro3_zm, etc)
            data = o3plots.Dataset(pt, **kwargs)
            ds = data.get_dataset(model)
            model_info_dict[pt]['data'] = ds.to_dict(data=False)

    logger.debug(F"{model} model info: {model_info_dict}")
    return model_info_dict

def get_plot_types():
    """Get list of the provided plot methods"""
    plots = [ TCO3, TCO3Return] #, VMRO3 ]

    return plots

#@_profile
@_catch_error
def plot_tco3_zm(*args, **kwargs):
    """Plot tco3_zm

    :param kwargs: provided in the API call parameters
    :return: Either PDF plot or JSON document
    """
    time_start = time.time()

    kwargs[PTYPE] = TCO3
    kwargs[MODELS] = phlp.cleanse_models(**kwargs)

    models_style = get_plot_style(**kwargs)
    # define plot styling for more curves (reference, mean, median)
    models_stats_style = [{ 'model': 'reference_value',
                            TCO3: { PLOT_ST: {'color': 'black', 
                                             'linestyle': 'dashed',
                                             'label': ('Reference value' + 
                                                       ' (' + 
                                                       str(kwargs['ref_year']) + 
                                                       ')')} 
                                  }
                          },
                          { 'model': 'MMMean',
                            TCO3: { PLOT_ST: {'color': 'green', 
                                             'linestyle': 'solid',
                                             'linewidth': 4 }
                                  }
                          },
                          { 'model': 'MMMean-Std',
                            TCO3: { PLOT_ST: {'color': 'green', 
                                             'linestyle': 'dotted',
                                             'linewidth': 1 }
                                  }
                          },
                          { 'model': 'MMMean+Std',
                            TCO3: { PLOT_ST: {'color': 'green', 
                                             'linestyle': 'dotted',
                                             'linewidth': 1 }
                                  }
                          },
                          { 'model': 'MMMedian',
                            TCO3: { PLOT_ST: {'color': 'blue', 
                                             'linestyle': 'dotted',
                                             'linewidth': 4 }
                                  }
                          },
                        ]

    models_style.extend(models_stats_style)

    ckwargs = __convert_plot_style(models_style, TCO3)
    # show lines, no marker, except REF_MEAS
    for model in ckwargs.keys():
        if model != kwargs[REF_MEAS]:
            ckwargs[model]['marker'] = ''

    data = o3plots.ProcessForTCO3(**kwargs)
    plot_data = data.get_ensemble_for_plot(kwargs[MODELS])

    logger.info(
       "[TIME] Time to prepare data for plotting: {}".format(time.time() -
                                                             time_start))
    if request.headers['Accept'] == "application/pdf":
        response = plot(plot_data, ckwargs, **kwargs)
    else:
        response = plot_json(plot_data, ckwargs, **kwargs)

    logger.info(
       "[TIME] Total time from getting the request: {}".format(time.time() -
                                                               time_start))
    return response

#@_catch_error
def plot_tco3_return(*args, **kwargs):
    """Plot tco3_return

    :param kwargs: provided in the API call parameters
    :return: Either PDF plot or JSON document
    """
    time_start = time.time()

    kwargs[PTYPE] = TCO3Return
    kwargs[MODELS] = phlp.cleanse_models(**kwargs)
    kwargs['begin'] = cfg.O3AS_TCO3Return_BEGIN_YEAR
    kwargs['end'] = cfg.O3AS_TCO3Return_END_YEAR
    user_month = kwargs['month']
    user_lat_min = kwargs['lat_min']
    user_lat_max = kwargs['lat_max']

    # initialize an empty pd.DataFrame
    plot_data = pd.DataFrame()
    # First draw pre-defined regions
    for r,p in cfg.tco3_return_regions.items():
        kwargs['region'] = r
        kwargs.update(p)
        #kwargs['lat_min'] = p['lat_min'] 
        #kwargs['lat_max'] = p['lat_max']
        if 'month' not in p.keys():
            kwargs['month'] = ''
        data = o3plots.ProcessForTCO3Return(**kwargs)
        data_return = data.get_ensemble_for_plot(kwargs[MODELS])
        plot_data = plot_data.append(data_return)

    # Then draw the user-defined region
    kwargs['region'] = 'User region'
    kwargs['month'] = user_month
    kwargs['lat_min'] = user_lat_min
    kwargs['lat_max'] = user_lat_max
    #('User region (' + str(kwargs['lat_min']) + ', ' + str(kwargs['lat_max']) + ')')
    data = o3plots.ProcessForTCO3Return(**kwargs)
    plot_data = plot_data.append(data.get_ensemble_for_plot(kwargs[MODELS]))

    # define plot styling for the mean
    models_style = get_plot_style(**kwargs)
    models_stats_style = [ { 'model': 'MMMean',
                             TCO3Return: { PLOT_ST: {'marker': '^',
                                                     'color': 'red',
                                                     'markersize': 14,
                                                     'mfc': 'none'} 
                                         }
                           },
                           { 'model': 'MMMean-Std',
                             TCO3Return: { PLOT_ST: {'marker': '_',
                                                     'color': 'red',
                                                     'markersize': 10,
                                                     'mfc': 'none'} 
                                         }
                           },
                           { 'model': 'MMMean+Std',
                             TCO3Return: { PLOT_ST: {'marker': '_',
                                                     'color': 'red',
                                                     'markersize': 10,
                                                     'mfc': 'none'} 
                                         }
                           },
                           { 'model': 'MMMedian',
                             TCO3Return: { PLOT_ST: {'marker': 'o',
                                                     'color': 'blue',
                                                     'markersize': 10,
                                                     'mfc': 'none'} 
                                         }
                           }
                         ]

    models_style.extend(models_stats_style)

    ckwargs = __convert_plot_style(models_style, TCO3Return)
    # show markers, no lines
    for model in ckwargs.keys():
        ckwargs[model]['linestyle'] = 'none'

    if request.headers['Accept'] == "application/pdf":
        # update MMMean plotstyle to plot with error bars
        cols = plot_data.columns
        mmmean_yerr = [ 0., 0.]
        if 'MMMean-Std' in cols and 'MMMean+Std' in cols:
            mmmean_yerr[0] = (plot_data['MMMean'] - plot_data['MMMean+Std'])
            mmmean_yerr[1] = (plot_data['MMMean-Std'] - plot_data['MMMean'])

        ckwargs['MMMean']['capsize'] = 6
        ckwargs['MMMean']['yerr'] = mmmean_yerr
        response = plot(plot_data, ckwargs, **kwargs)
    else:
        response = plot_json(plot_data, ckwargs, **kwargs)

    logger.info(
       "[TIME] Total time from getting the request: {}".format(time.time() -
                                                               time_start))
    return response

@_catch_error
def plot_vmro3_zm(*args, **kwargs):
    """Plot vmro3_zm

    :param kwargs: provided in the API call parameters
    :return: Either PDF plot or JSON document
    """
    kwargs[PTYPE] = "vmro3_zm"
    data = None
    models_info = get_models_info()
    ckwargs = None
    response = plot(data, ckwargs, **kwargs)

    return response

#@_profile
#@flaat.login_required() # Require only authorized people to call the function
def plot(data, ckwargs, **kwargs):
    """Main plotting routine

    :param data: data to plot
    :param ckwargs: dictionary for curve plotting (e.g. color, style)
    :param kwargs: provided in the API call parameters
    :return: PDF plot
    """
    plot_type = kwargs[PTYPE]
    # update the list of models as columns from pd.DataFrame
    # as additional columns can be added, e.g. 'reference_year', 'mean' etc
    models = data.columns

    logger.debug(F"headers: {dict(request.headers)}")
    logger.debug(F"kwargs: {kwargs}")
  
    def __return_plot(df, model):
        """Function to draw the plot

        :param df: data (pandas.DataFrame) to process
        :param model: model to process
        """

        if model != 'MMMean-Std' and model != 'MMMean+Std':
            df[model].plot(**ckwargs[model]) #.dropna()
  

    figure_file = phlp.set_filename(**kwargs) + ".pdf"
    fig = plt.figure(num=None, figsize=(plot_c[plot_type]['fig_size']), 
                     dpi=150, facecolor='w',
                     edgecolor='k')

    [ __return_plot(data, m) for m in models ]
        
    if plot_type == TCO3:        
        if 'MMMean-Std' in models and 'MMMean+Std' in models:
            plt.fill_between(data.index, 
                             data['MMMean-Std'],
                             data['MMMean+Std'],
                             color='green', alpha=0.2)

    phlp.set_figure_attr(fig, **kwargs)

    buffer_plot = BytesIO()  # store in IO buffer, not a file
    plt.savefig(buffer_plot, format='pdf', bbox_inches='tight')
    plt.close(fig)
    buffer_plot.seek(0)

    response = send_file(buffer_plot,
                         as_attachment=True,
                         attachment_filename=figure_file,
                         mimetype='application/pdf')

    return response

def plot_json(data, ckwargs, **kwargs):
    """Plotting routine returning JSON points

    :param data: data ready for plotting
    :param ckwargs: dictionary for curve plotting (e.g. color, style)
    :param kwargs: provided in the API call parameters
    :return: JSON document with data points and styles for plotting
    """
    plot_type = kwargs[PTYPE]
    # update the list of models as columns from pd.DataFrame
    # as additional columns can be added, e.g. 'reference_year', 'mean' etc
    models = data.columns

    logger.debug(F"headers: {dict(request.headers)}")
    logger.debug(F"kwargs: {kwargs}")

    models = data.columns
    json_output = []
    __json_append = json_output.append
    [ __json_append(__return_json(data, m, ckwargs[m])) for m in models ]
        
    return json_output  