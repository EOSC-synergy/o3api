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


import o3as.config as cfg
import o3as.plothelpers as phlp
import o3as.plots as o3plots
import json
import logging
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
from statsmodels.tsa.seasonal import seasonal_decompose # accurate enough

# conigure python logger
logger = logging.getLogger('__name__') #o3asplot
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
logger.setLevel(cfg.log_level)

## Authorization
from flaat import Flaat
flaat = Flaat()

# list of trusted OIDC providers
flaat.set_trusted_OP_list(cfg.trusted_OP_list)

# configuration for plotting
pconf = cfg.plot_conf


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

@_catch_error
def get_metadata(*args, **kwargs):
    """Return information about the package

    :return: The o3as package info
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
    plot_type = kwargs['type']
    model = kwargs['model'].lstrip().rstrip()

    # create dataset according to the plot type (tco3_zm, vmro3_zm, etc)
    data = o3plots.Dataset(plot_type, **kwargs)
    ds = data.get_dataset(model)
      
    info_dict = ds.to_dict(data=False)
    info_dict['model'] = model

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
    plot_type = kwargs['type']
    models = kwargs['models']
    time_start = time.time()

    logger.debug(F"headers: {dict(request.headers)}")
    logger.info(F"kwargs: {kwargs}")

    def __get_curve(data, model, plot_type):
        """Function to get curve for the model
        
        :param data: pointer to how process data
        :param model: model to process
        :return: curve
        :rtype: pandas Series
        """

        time_model = time.time()
        # strip possible spaces in front and back
        model = model.lstrip().rstrip()
        logger.debug(F"model = {model}")

        # get data for the plot
        data_processed = __get_plot_data(model)
 
        # convert to pandas series to keep date information
        if (type(data_processed.indexes['time']) is 
            pd.core.indexes.datetimes.DatetimeIndex) :
            time_axis = data_processed.indexes['time'].values
        else:
            time_axis = data_processed.indexes['time'].to_datetimeindex()

        curve = pd.Series(np.nan_to_num(data_processed[plot_type]), 
                          index=pd.DatetimeIndex(time_axis),
                          name=model )

        time_described = time.time()
        logger.debug("[TIME] One model processed: {}".format(time_described - 
                                                             time_model))                          
        return curve

   
    def __return_json(data, model, plot_type):
        """Function to return JSON
        """

        curve = __get_curve(data, model, plot_type)
        observed = {"model": model,
                    "x": curve.index.tolist(),
                    "y": curve.values.tolist(),
                   }
        return observed
        

    def __return_pdf(data, model, plot_type):
        """Function to return PDF plot
        """
        curve = __get_curve(data, model, plot_type)
        curve.plot()
        time_axis = curve.index
        periodicity = phlp.get_periodicity(time_axis)
        logger.info("Data periodicity: {} points/year".format(periodicity))
        decompose = seasonal_decompose(curve, period=periodicity)
        trend = pd.Series(decompose.trend, 
                          index=time_axis,
                          name=model+" (trend)" )
        trend.plot()        
        

    # set how to process data (tco3_zm, vmro3_zm, etc)
    data = o3plots.set_data_processing(plot_type, **kwargs)
    __get_plot_data = data.get_plot_data
    json_output = []
    __json_append = json_output.append

    if request.headers['Accept'] == "application/pdf":
        fig = plt.figure(num=None, figsize=(pconf[plot_type]['fig_size']), 
                         dpi=150, facecolor='w',
                         edgecolor='k')
                         
        [ __return_pdf(data, m, plot_type) for m in models ]

        figure_file = phlp.set_filename(**kwargs) + ".pdf"
        plt.title(phlp.set_plot_title(**kwargs))
        plt.legend()
        buffer_plot = BytesIO()  # store in IO buffer, not a file
        plt.savefig(buffer_plot, format='pdf')
        plt.close(fig)
        buffer_plot.seek(0)

        response = send_file(buffer_plot,
                             as_attachment=True,
                             attachment_filename=figure_file,
                             mimetype='application/pdf')
    else:

        fig_type = {"plot_type": plot_type}
        __json_append(fig_type)
    
        [ __json_append(__return_json(data, m, plot_type)) for m in models ]
        
        response = json_output

    logger.info(
       "[TIME] Total time from getting the request: {}".format(time.time() -
                                                               time_start))
    
    return response
