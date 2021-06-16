# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
"""
Created on Tue December 8 13:47:51 2020
@author: vykozlov
"""
import logging
import numpy as np
import os
import pytest
import unittest
from o3api import api as o3api
from o3api import config as cfg

import flask
import connexion
import json

# conigure python logge
logger = logging.getLogger('__name__') #o3api
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
logger.setLevel(logging.DEBUG)

# configuration for netCDF
TIME = 'time'
LAT  = 'lat'
TCO3 = 'tco3_zm'
VMRO3 = 'vmro3_zm'
TCO3Return = 'tco3_return'

# API configuration
PTYPE = 'ptype'
MODELS = 'models'
BEGIN = 'begin'
END = 'end'
MONTH = 'month'
LAT_MIN = 'lat_min'
LAT_MAX = 'lat_max'
REF_MEAS = 'ref_meas'
REF_YEAR = 'ref_year'

class TestAPIMethods(unittest.TestCase):

    def setUp(self):
        specification_path = os.path.join(cfg.O3API_BASE_DIR, "o3api")
        app = connexion.FlaskApp(__name__, 
                                 specification_dir=specification_path)
        # Read the swagger.yml file to configure the endpoints
        app.add_api('swagger.yml')
        self.client = app.app.test_client()
        self.headers = {'Content-Type': 'application/json',
                        'Accept': 'application/json'}
                        
        self.models = ['test-o3api', 'test-o3api-2', 'test-o3api-3']
        self.ref_meas = 'test-ref-model'
        self.ref_year = 1980
        cfg.O3AS_DATA_BASEPATH = "tmp/data"
        cfg.O3AS_TCO3_REF_MEAS = self.ref_meas
        cfg.O3AS_TCO3_REF_YEAR = self.ref_year

        begin_year = 1970
        end_year = begin_year + 70 # default boxcar is 10(years), range>boxcar

        data_tco3_query_dict = { BEGIN: str(begin_year), 
                                 END:   str(end_year),
                                 LAT_MIN: '-10',
                                 LAT_MAX: '10'
                               }
        request_q = ''.join([key + "=" + val + "&" 
                             for key,val in data_tco3_query_dict.items()])
        self.data_tco3_request_q = request_q[:-1] + ''

        self.tco3_body = list(self.models)
        plots_tco3_query_dict = { BEGIN: str(begin_year), 
                                  END:   str(end_year),
                                  LAT_MIN: '-10',
                                  LAT_MAX: '10',
                                  REF_MEAS: self.ref_meas,
                                  REF_YEAR: str(self.ref_year)
                                }
        request_q = ''.join([key + "=" + val + "&" 
                             for key,val in plots_tco3_query_dict.items()])
        self.plots_tco3_request_q = request_q[:-1] + ''


    def test_api_info(self):
        meta = self.client.get('/api/v1/apiinfo')
        logger.debug(F"[API] meta = {meta.data}")
        logger.debug(F"[API] type(meta.data) = {type(meta.data)}")
        self.assertEqual(200, meta.status_code)
        #self.assertTrue(type(meta.data) is dict)

    def test_api_data(self):
        ptypes = self.client.get('/api/v1/data')
        self.assertEqual(200, ptypes.status_code)

    def test_api_data_tco3_zm(self):
        logger.info(F"[API] plot_tco3: {self.plots_tco3_request_q}")
        # WHY json=json.dumps(request_j) does NOT work?!?!?!
        data = self.client.post('/api/v1/data/tco3_zm',
                                headers=self.headers,
                                data=json.dumps(self.tco3_body),
                                query_string=self.data_tco3_request_q
                               )
        logger.debug(F"[API] data_tco3.data: {data.data}")
        logger.debug(F"[API] data_tco3.content_type: {data.content_type}")
        self.assertEqual(200, data.status_code)

    def test_api_data_tco3_return(self):
        logger.info(F"[API] plot_tco3: {self.plots_tco3_request_q}")
        # WHY json=json.dumps(request_j) does NOT work?!?!?!
        data = self.client.post('/api/v1/data/tco3_return',
                                headers=self.headers,
                                data=json.dumps(self.tco3_body),
                                query_string=self.data_tco3_request_q
                               )
        logger.debug(F"[API] data_tco3.data: {data.data}")
        logger.debug(F"[API] data_tco3.content_type: {data.content_type}")
        self.assertEqual(200, data.status_code)

    def test_api_models(self):
        models = self.client.get('/api/v1/models')
        logger.debug(F"[API] models = {models.data}")
        logger.debug(F"[API] type(models.data) = {type(models.data)}")
        self.assertEqual(200, models.status_code)
        
    #def test_api_models_list(self):
    #    request_j = { 'select': '' }
    #    request_q = ''.join([key + "=" + val + "&" for key,val in request_j.items()])
    #    request_q = request_q[:-1] + ''
    #    api_method = os.path.join('/api/models/list', 'all')
    #    models = self.client.post(api_method,
    #                              headers=self.headers,
    #                              query_string=request_q
    #                              )
    #    logger.info(F"[API] models (list) = {models.data}")
    #    self.assertEqual(200, models.status_code)

    def test_api_model_info(self):
        m_path = os.path.join('/api/v1/models/', self.models[0])
        m_info = self.client.get(m_path, headers=self.headers)
        logger.debug(F"[API] m_info.data: {m_info.data}")
        logger.debug(F"[API] m_info.content_type: {m_info.content_type}")
        self.assertEqual(200, m_info.status_code)

    def test_api_plots(self):
        models = self.client.get('/api/v1/plots')
        self.assertEqual(200, models.status_code)

    def test_api_plots_tco3_zm(self):
        logger.info(F"[API] plot_tco3: {self.plots_tco3_request_q}")
        # WHY json=json.dumps(request_j) does NOT work?!
        plot = self.client.post('/api/v1/plots/tco3_zm',
                                headers=self.headers,
                                data=json.dumps(self.tco3_body),
                                query_string=self.plots_tco3_request_q
                               )
        logger.debug(F"[API] plot_tco3.data: {plot.data}")
        logger.debug(F"[API] plot_tco3.content_type: {plot.content_type}")
        self.assertEqual(200, plot.status_code)

    def test_api_plots_tco3_return(self):
        logger.info(F"[API] plot_return: {self.plots_tco3_request_q}")
        # WHY json=json.dumps(request_j) does NOT work?!
        plot = self.client.post('/api/v1/plots/tco3_return',
                                headers=self.headers,
                                data=json.dumps(self.tco3_body),
                                query_string=self.plots_tco3_request_q
                               )
        logger.debug(F"[API] plot_return.data: {plot.data}")
        logger.debug(F"[API] plot_return.content_type: {plot.content_type}")
        self.assertEqual(200, plot.status_code)

if __name__ == '__main__':
    unittest.main()
