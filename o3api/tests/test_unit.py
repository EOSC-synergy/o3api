# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
"""
Created on Sat June 30 23:47:51 2020
@author: vykozlov
"""
import logging
import numpy as np
import os
import pandas as pd
import pytest
import xarray as xr
import yaml
#import time
import unittest
from o3api import api as o3api
from o3api import config as cfg
from o3api import plots as o3plots
from o3api import plothelpers as phlp

#import json

# conigure python logger
logger = logging.getLogger('__name__') #o3api
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
logger.setLevel(logging.INFO)

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

@pytest.mark.run(order=1)
class TestPackageMethods(unittest.TestCase):

    def setUp(self):

        self.models = ['test-o3api', 'test-o3api-2', 'test-o3api-3']
        self.ref_meas = 'test-ref-model'
        self.ref_year = 1980
        # Check package meta info
        self.meta = {
            'name' : 'o3api',
            'version' : None,
            'summary' : 'REST API for the O3as service to analyse Ozone projections',
            'home-page' : 'https://git.scc.kit.edu/synergy.o3as/o3api',
            'author' : 'KIT-IMK, KIT-SCC',
            'author-email' : 'tobias.kerzenmacher@kit.edu, borja.sanchis@kit.edu, valentin.kozlov@kit.edu',
            'license' : 'GNU LGPLv3'
        }

        # Create artificial data and store it
        self.start_date = np.datetime64('1970-01-01T00:00:00Z', 'M')
        self.end_date = np.datetime64('2100-12-31T00:00:00Z', 'M')
        delta_years = 131

        ### example of a more complicated dataset        
        #self.o3ds = xr.Dataset(
        #    {"t": (("level", "lat", "time"), np.ones((10, 19, 24))),
        #     "tco3_zm": (("level", "lat", "time"), np.ones((10, 19, 24))),
        #    },
        #    coords={
        #            "level": [z for z in range(0, 1000, 100)],
        #            "lat": [x for x in range(-90, 100, 10)],
        #            "time": [ self.start_date + np.timedelta64(x, 'M') 
        #                      for x in range(0, 12*delta_years, 1)]
        #           }
        #)
        ###

        data_base_path = 'tmp/data'
        ptype = TCO3
        #os.environ["O3API_DATA_BASEPATH"] = self.data_base_path
        cfg.O3AS_DATA_BASEPATH = data_base_path
        cfg.O3AS_TCO3_REF_MEAS = self.ref_meas
        cfg.O3AS_TCO3_REF_YEAR = self.ref_year

        # metadata
        self.metayaml = {TCO3: {'plotstyle': { 'color': 'black',
                                               'marker': 'o',
                                               'linestyle': 'solid' }},
                         TCO3Return: {'plotstyle': { 'color': 'black',
                                                     'marker': 'o',
                                                     'linestyle': 'solid' }},
                         VMRO3: {'plotstyle': { 'color': 'black',
                                                'marker': 'o',
                                                'linestyle': 'solid' }}
                        }

        ### dummy reference dataset, monthly data
        self.o3ds_ref = xr.Dataset(
            {TCO3: ((LAT, TIME), np.ones((19, 12*delta_years))/2.),
            },
            coords={
                    LAT : [x for x in range(-90, 100, 10)],
                    TIME: [ self.start_date + np.timedelta64(x, 'M')
                             for x in range(0, 12*delta_years, 1)]
                   }
        )
        ref_dir = os.path.join(data_base_path, self.ref_meas)
        ref_path  = os.path.join(ref_dir, ptype + '-ref' + '.nc')
        os.makedirs(ref_dir, exist_ok=True)
        self.o3ds_ref.to_netcdf(ref_path)
        self.o3ds_ref.close()

        with open(os.path.join(ref_dir, 'metadata.yaml'), 'w') as file:
            yaml.dump(self.metayaml, file, default_flow_style=False)
            
        ### function to emulate monthly data with noise:
        def __tco3_one(months):
            noise = np.random.normal(0, .125, months)
            x = np.arange(months)
            y = 0.25*(np.cos(2 * np.pi * x / months) + noise) + 0.4
            return y

        ### tco3 dataset, monthly data
        for m in self.models:
            tco3 = np.zeros((19, delta_years*12))
            for l in range(0,19):
                tco3[l, :] = __tco3_one(delta_years*12)
            self.o3ds = xr.Dataset(
                {TCO3: ((LAT, TIME), tco3) },
                coords={
                        LAT : [x for x in range(-90, 100, 10)],
                        TIME: [ self.start_date + np.timedelta64(x, 'M') 
                                  for x in range(0, 12*delta_years, 1)]
                       }
            )

            end_year = self.end_date.astype('datetime64[Y]').astype(int) + 1970
            begin_year = self.start_date.astype('datetime64[Y]').astype(int) + 1970

            test_dir = os.path.join(data_base_path, m)
            test_path  = os.path.join(test_dir, ptype + "-test-" + 
                                      str(end_year) + ".nc")
            os.makedirs(test_dir, exist_ok=True)
            self.o3ds.to_netcdf(test_path)
            self.o3ds.close()
        
            with open(os.path.join(test_dir, 'metadata.yaml'), 'w') as file:
                yaml.dump(self.metayaml, file)

        #time.sleep(1) # wait untin file is written?

        self.kwargs = {
            PTYPE : ptype,
            MODELS: self.models,
            BEGIN: begin_year,
            END  : end_year,
            MONTH: '',
            LAT_MIN: -10,
            LAT_MAX: 10,
            REF_MEAS: self.ref_meas,
            REF_YEAR: self.ref_year
        }

        logger.info(F"kwargs: {self.kwargs}")

        # initialize how to process data
        self.data = o3plots.ProcessForTCO3(**self.kwargs)
            
        # initialize the plot title and filename
        deg_sign= u'\N{DEGREE SIGN}'
        self.plot_title = ('requested: ' +
                           self.kwargs[PTYPE] + ', ' +
                           str(self.kwargs[BEGIN]) + '..' +
                           str(self.kwargs[END]) + ', ' +
                           'full_year' + ', latitudes: ' +
                           str(self.kwargs[LAT_MIN]) + deg_sign + '..' +
                           str(self.kwargs[LAT_MAX]) + deg_sign )

        self.plot_filename = (self.kwargs[PTYPE] + '_' + 
                              str(self.kwargs[BEGIN]) + '_' +
                              str(self.kwargs[END]) + '_' +
                              'full_year' + '_' +
                              str(self.kwargs[LAT_MIN]) + '_' +
                              str(self.kwargs[LAT_MAX]) + '_' +
                              self.ref_meas + '_' + str(self.ref_year))


    def test_metadata_type(self):
        """
        Test that o3meta is dict
        """
        o3meta = o3api.get_api_info()
        self.assertTrue(type(o3meta) is dict)


    def test_api_info_values(self):
        """
        Test that metadata contains right values (subset)
        """
        o3meta = o3api.get_api_info()
        self.assertEqual(self.meta['name'].replace('-','_'),
                         o3meta['name'].replace('-','_'))
        self.assertEqual(self.meta['summary'].replace('-','_'),
                         o3meta['summary'].replace('-','_'))
        self.assertEqual(self.meta['home-page'].lower().replace(' ',''),
                         o3meta['home-page'].lower().replace(' ',''))
        self.assertEqual(self.meta['author'].lower().replace(' ',''),
                         o3meta['author'].lower().replace(' ',''))
        self.assertEqual(self.meta['author-email'].lower().replace(' ',''), 
                         o3meta['author-email'].lower().replace(' ',''))
        self.assertEqual(self.meta['license'].lower(),
                         o3meta['license'].lower())

    def test_get_data_type(self):
        """
        Test that list of data types is list
        """
        o3data = o3api.get_data_types()
        self.assertTrue(type(o3data) is list)

    def test_models_list(self):
        """
        Test that list of models is list
        """
        kwargs = {}
        kwargs[PTYPE] = TCO3
        kwargs['select'] = ''
        o3list = o3api.get_models_list(**kwargs)
        self.assertTrue(type(o3list) is list)

    def test_get_models_info_type(self):
        """
        Test that models_info is list, where a member is dict 
        """
        o3models_info = o3api.get_models_info()
        self.assertTrue(type(o3models_info) is list)
        self.assertTrue(type(o3models_info[0]) is dict)

    def test_get_model_detail_type(self):
        """
        Test that model detail is dict
        """
        o3kwargs = {
            'model': self.kwargs[MODELS][0]
        }
        o3model_detail = o3api.get_model_detail(**o3kwargs)
        self.assertTrue(type(o3model_detail) is dict)

    def test_get_dataset_values(self):
        """
        Test that returned dataset values are the same as generated.
        """
        model = self.kwargs[MODELS][0]
        ds = self.data.get_dataset(model)
        self.assertEqual(ds, self.o3ds)

    def test_get_dataslice_type(self):
        """
        Test that the returned dataset type is correct, xarray.Dataset
        """
        model = self.kwargs[MODELS][0]
        ds = self.data.get_dataslice(model)
        self.assertTrue(type(ds) is xr.Dataset)

    def test_check_datasliece_lat(self):
        """
        Test if latitudes are correct for the selected slice
        """
        lat_min = self.kwargs[LAT_MIN]
        lat_max = self.kwargs[LAT_MAX]

        model = self.kwargs[MODELS][0]
        ds = self.data.get_dataslice(model)
        
        lat_0 = np.amin(ds.coords[LAT].values[0]) # min latitude
        lat_last = np.amax(ds.coords[LAT].values[-1]) # max latitude
        
        self.assertEqual([lat_min, lat_max], [lat_0, lat_last])

    def test_get_data_pd_type(self):
        """
        Test that the returned data type is correct, pd.DataFrame
        """
        model = self.kwargs[MODELS][0]
        ds = self.data.get_raw_data_pd(model)
        self.assertTrue(type(ds) is pd.DataFrame)

    def test_get_ensemble_pd_type(self):
        """
        Test that the returned data type is correct, pd.DataFrame
        """
        models = self.kwargs[MODELS]
        ds = self.data.get_raw_ensemble_pd(models)
        self.assertTrue(type(ds) is pd.DataFrame)

    def test_get_ref_value(self):
        """
        Test that get_ref_value() is correct
        """
        ref_value = self.data.get_ref_value()
        logger.info(F"ref_value: {ref_value}")
        self.assertTrue(ref_value == 0.5)

    def test_get_date_range(self):
        """
        Test correctness of returned min/max dates
        """
        date_min, date_max = phlp.get_date_range(self.o3ds)
        self.assertEqual(date_min, self.start_date)
        self.assertEqual(date_max, self.end_date)

    def test_get_periodicity(self):
        """
        Test correctness of returned periodicity
        """
        time_axis = pd.DatetimeIndex(self.o3ds.coords[TIME].values)
        period = phlp.get_periodicity(time_axis)
        self.assertEqual(period, 12)
        
    def test_get_plot_filename(self):
        """
        Test setting of the plot filename
        """
        o3plot_filename = phlp.set_filename(**self.kwargs)
        self.assertEqual(self.plot_filename, o3plot_filename)

    def test_get_plot_title(self):
        """
        Test setting of the plot title
        """
        o3plot_title = phlp.set_plot_title(**self.kwargs)
        self.assertEqual(self.plot_title, o3plot_title)


#class TestTCO3ReturnMethods(TestPackageMethods):


if __name__ == '__main__':
    unittest.main()
