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
import time

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
MODEL = cfg.api_conf['model']
BEGIN = cfg.api_conf['begin']
END = cfg.api_conf['end']
MONTH = cfg.api_conf['month']
LAT_MIN = cfg.api_conf['lat_min']
LAT_MAX = cfg.api_conf['lat_max']

# configuration for plotting
plot_c = cfg.plot_conf


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
        logger.debug("[TIME] One model processed: {}".format(time_described - 
                                                             time_model))
        return f
    return wrap

@_catch_error
def get_metadata(*args, **kwargs):
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
def list_models(*args, **kwargs):
    """Return the list of available Ozone models

    :return: The list of available models
    :rtype: dict
    """
    models = []
    for mdir in os.listdir(cfg.O3AS_DATA_BASEPATH):
        m_path = os.path.join(cfg.O3AS_DATA_BASEPATH, mdir)
        if (os.path.isdir(m_path)):
            netcdf_ok = False
            for f in os.listdir(m_path):
                if ".nc" in f:
                    netcdf_ok = True
            models.append(mdir) if netcdf_ok else ''
    
    models.sort()
    models_dict = { "models": models }
    logger.debug(F"Model list: {models_dict}")

    return models_dict

@_catch_error
def get_model_info(*args, **kwargs):
    """Return information about the Ozone model

    :return: Info about the Ozone model
    :rtype: dict
    """
    plot_type = kwargs[PTYPE]
    model = kwargs[MODEL].lstrip().rstrip()

    # create dataset according to the plot type (tco3_zm, vmro3_zm, etc)
    data = o3plots.Dataset(plot_type, **kwargs)
    ds = data.get_dataset(model)
      
    info_dict = ds.to_dict(data=False)
    info_dict[MODEL] = model

    logger.debug(F"{model} model info: {info_dict}")
    return info_dict

#@_profile
@flaat.login_required() # Require only authorized people to call api method   
@_catch_error
def plot(*args, **kwargs):
    """Main plotting routine

    :param kwargs: The provided in the API call parameters
    :return: Either PDF plot or JSON document
    """
    plot_type = kwargs[PTYPE]
    models = phlp.clean_models(**kwargs)
    time_start = time.time()

    logger.debug(F"headers: {dict(request.headers)}")
    logger.info(F"kwargs: {kwargs}")

    # set how to process data (tco3_zm, vmro3_zm, etc)
    data = o3plots.set_data_processing(plot_type, **kwargs)
    __get_raw_data = data.get_raw_data
    __get_plot_data = data.get_plot_data
    __get_ref1980 = data.get_ref1980

    @_timeit
    def __return_json(model):
        """Function to return JSON

        :param model: model to process
        :return: JSON with points (x,y)
        """
        curve = __get_raw_data(model)
        observed = { MODEL: model,
                    "x": curve.index.tolist(),
                    "y": curve.values.tolist(),
                   }
        return observed

    @_timeit
    def __return_plot(model):
        """Function to draw the plot

        :param model: model to process
        """
        curve = __get_plot_data(model)
        curve.plot()

    if request.headers['Accept'] == "application/pdf":
        figure_file = phlp.set_filename(**kwargs) + ".pdf"
        fig = plt.figure(num=None, figsize=(plot_c[plot_type]['fig_size']), 
                         dpi=150, facecolor='w',
                         edgecolor='k')

        [ __return_plot(m) for m in models ]

        #phlp.set_figure_attr(fig, **kwargs)

        values1980 = [ __get_ref1980(m) for m in models ]
        ref1980 = np.nanmean(values1980)
        xmin, xmax = plt.xlim()
        plt.hlines(ref1980, xmin, xmax, 
                   colors='k', # 'dimgray'..? 
                   linestyles='dashed',
                   zorder=256) # big zorder for above all 
        logger.debug(F"ref1980 values: {values1980} and the mean: {ref1980}")

        phlp.set_figure_attr(fig, **kwargs)

        buffer_plot = BytesIO()  # store in IO buffer, not a file
        plt.savefig(buffer_plot, format='pdf', bbox_inches='tight')
        plt.close(fig)
        buffer_plot.seek(0)

        response = send_file(buffer_plot,
                             as_attachment=True,
                             attachment_filename=figure_file,
                             mimetype='application/pdf')
    else:
        json_output = []
        __json_append = json_output.append

        fig_type = { PTYPE: plot_type}
        __json_append(fig_type)
    
        [ __json_append(__return_json(m)) for m in models ]
        
        response = json_output

    logger.info(
       "[TIME] Total time from getting the request: {}".format(time.time() -
                                                               time_start))
    return response
