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
import numpy as np
import os
import pytest
import unittest
from o3api import api as o3api
from o3api import config as cfg

import flask
import connexion
import json

# configuration for netCDF
TIME = 'time'
LAT  = 'lat'
TCO3 = 'tco3_zm'
VMRO3 = 'vmro3_zm'
TCO3Return = 'tco3_return'

# configuration for API
PTYPE  = 'ptype'
MODEL = 'model'
BEGIN = 'begin'
END   = 'end'
MONTH = 'month'
LAT_MIN = 'lat_min'
LAT_MAX = 'lat_max'


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
        cfg.O3AS_DATA_BASEPATH = "tmp/data"
        
    def test_api_get_metadata(self):
        meta = self.client.post('/api/get_metadata')
        print(F"[API] meta = {meta.data}")
        print(F"[API] type(meta.data) = {type(meta.data)}")
        self.assertEqual(200, meta.status_code)
        #self.assertTrue(type(meta.data) is dict)

    def test_api_model_info(self):
        request_j = { PTYPE: TCO3, MODEL: 'o3api-test' }
        request_q = ''.join([key + "=" + val + "&" for key,val in request_j.items() ])
        request_q = request_q[:-1] + ''
        # WHY json=json.dumps(request_j) does NOT work?!?!?!
        m_info = self.client.post('/api/get_model_info',
                                  headers=self.headers,
                                  query_string=request_q
                                  )
        print(F"[API] m_info.data: {m_info.data}")
        print(F"[API] m_info.content_type: {m_info.content_type}")
        self.assertEqual(200, m_info.status_code)

    def test_api_list_models(self):
        models = self.client.post('/api/list_models')
        print(F"[API] models = {models.data}")
        print(F"[API] type(models.data) = {type(models.data)}")
        self.assertEqual(200, models.status_code)

    def test_api_plot(self):
        
        end_year = np.datetime64('today', 'Y').astype(int) + 1970
        begin_year = end_year - 2
        request_j = { PTYPE: TCO3, 
                      MODEL: 'o3api-test', 
                      BEGIN: str(begin_year), 
                      END:   str(end_year),
                      LAT_MIN: '-10',
                      LAT_MAX: '10'
                    }
        request_q = ''.join([key + "=" + val + "&" for key,val in request_j.items()])
        request_q = request_q[:-1] + ''
        print(F"[API], plot: {request_q}")
        # WHY json=json.dumps(request_j) does NOT work?!?!?!
        plot = self.client.post('/api/plot',
                                  headers=self.headers,
                                  #json=json.dumps(request_j)
                                  query_string=request_q
                                  )
        print(F"[API] plot.data: {plot.data}")
        print(F"[API] plot.content_type: {plot.content_type}")
        self.assertEqual(200, plot.status_code)

if __name__ == '__main__':
    unittest.main()
