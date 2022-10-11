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
import unittest

from o3api import config as cfg
from o3api import api as o3api
from o3api import load as o3load
from o3api import prepare as o3prepare
from o3api import tco3_zm as tco3zm
from o3api import plothelpers as phlp

# conigure python logger
logger = logging.getLogger('__name__')
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
REF_FILLNA = 'ref_fillna'

data_base_path = 'tmp/data'
cfg.O3AS_DATA_BASEPATH = data_base_path

@pytest.mark.run(order=1)
class TestPackageMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.models = ['test-o3api', 'test-o3api-2', 'test-o3api-3']
        cls.ref_meas = 'test-ref-model'
        cls.ref_year = 1980
        # Check package meta info
        cls.meta = {
            'name' : 'o3api',
            'version' : None,
            'summary' : 'REST API for the O3as service to analyse Ozone projections',
            'home-page' : 'https://git.scc.kit.edu/synergy.o3as/o3api',
            'author' : 'KIT-IMK-ASF, KIT-SCC',
            'author-email' : 'tobias.kerzenmacher@kit.edu, borja.sanchis@kit.edu, valentin.kozlov@kit.edu',
            'license' : 'GNU LGPLv3'
        }

        # Create artificial data and store it
        cls.start_date = np.datetime64('1970-01-01T00:00:00Z', 'M')
        cls.end_date = np.datetime64('2100-12-31T00:00:00Z', 'M')
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

        ptype = TCO3

        cls.fake_email = 'no-reply@fakeaddress.domain'

        # metadata
        cls.o3meta = {
                      TCO3: {'plotstyle': { 'color': 'black',
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
        cls.o3ds_ref = xr.Dataset(
            {TCO3: ((LAT, TIME), np.ones((19, 12*delta_years))/2.),
            },
            coords={
                    LAT : [x for x in range(-90, 100, 10)],
                    TIME: [ cls.start_date + np.timedelta64(x, 'M')
                             for x in range(0, 12*delta_years, 1)]
                   }
        )
        ref_dir = os.path.join(data_base_path, cls.ref_meas)
        ref_path  = os.path.join(ref_dir, ptype + '-ref' + '.nc')
        os.makedirs(ref_dir, exist_ok=True)
        cls.o3ds_ref.to_netcdf(ref_path)
        cls.o3ds_ref.close()

        with open(cfg.O3AS_DATA_SOURCES_CSV, 'w') as file:
            file.write("source,model,parameter,Conventions,plot_color,plot_linestyle,plot_marker\n")
            for model in cls.models:
                color = cls.o3meta[ptype]['plotstyle']['color']
                linestyle = cls.o3meta[ptype]['plotstyle']['linestyle']
                marker = cls.o3meta[ptype]['plotstyle']['marker']
                file.write(F"test,{model},{ptype},CF-1.4,{color},{linestyle},{marker}\n")

        ### function to emulate monthly data with noise:
        def __tco3_one(months):
            noise = np.random.normal(0, .125, months)
            x = np.arange(months)
            y = 0.25*(np.cos(2 * np.pi * x / months) + noise) + 0.4
            return y

        ### tco3 dataset, monthly data
        for m in cls.models:
            tco3 = np.zeros((19, delta_years*12))
            for l in range(0,19):
                tco3[l, :] = __tco3_one(delta_years*12)
            cls.o3ds = xr.Dataset(
                {TCO3: ((LAT, TIME), tco3) },
                coords={
                        LAT : [x for x in range(-90, 100, 10)],
                        TIME: [ cls.start_date + np.timedelta64(x, 'M')
                                  for x in range(0, 12*delta_years, 1)]
                       },
                attrs={
                        'Conventions': 'CF-1.4',
                        'comment': 'test data in '+ m,
                        'contact': cls.fake_email,
                        'experiment': 'Projection',
                      }
            )

            end_year = cls.end_date.astype('datetime64[Y]').astype(int) + 1970
            begin_year = cls.start_date.astype('datetime64[Y]').astype(int) + 1970

            test_dir = os.path.join(data_base_path, m)
            test_path  = os.path.join(test_dir, ptype + "-test-" +
                                      str(end_year) + ".nc")
            os.makedirs(test_dir, exist_ok=True)
            cls.o3ds.to_netcdf(test_path)
            cls.o3ds.close()

        #time.sleep(1) # wait untin file is written?

        cls.kwargs = {
            PTYPE : ptype,
            MODELS: cls.models,
            BEGIN: begin_year,
            END  : end_year,
            MONTH: '',
            LAT_MIN: -10,
            LAT_MAX: 10,
            REF_MEAS: cls.ref_meas,
            REF_YEAR: cls.ref_year,
            REF_FILLNA: True
        }

        logger.info(F"kwargs: {cls.kwargs}")

        # dictionary to load O3as data in memory (in o3api!)
        o3api.o3data = {
                ptype: o3load.LoadData(cfg.O3AS_DATA_BASEPATH,
                                       "tco3_zm").load_dataset_ensemble()
        }

        # initialize how to process data
        cls.rdata = o3prepare.PrepareData(o3api.o3data[ptype], **cls.kwargs)

        # initialize how to process (plot) data
        cls.pdata = tco3zm.ProcessForTCO3Zm(o3api.o3data[ptype], **cls.kwargs)

        # initialize the plot title and filename
        deg_sign= u'\N{DEGREE SIGN}'
        cls.plot_title = ('requested: ' +
                           cls.kwargs[PTYPE] + ', ' +
                           str(cls.kwargs[BEGIN]) + '..' +
                           str(cls.kwargs[END]) + ', ' +
                           'full_year' + ', latitudes: ' +
                           str(cls.kwargs[LAT_MIN]) + deg_sign + '..' +
                           str(cls.kwargs[LAT_MAX]) + deg_sign )

        cls.plot_filename = (cls.kwargs[PTYPE] + '_' +
                             str(cls.kwargs[BEGIN]) + '_' +
                             str(cls.kwargs[END]) + '_' +
                                 'full_year' + '_' +
                             str(cls.kwargs[LAT_MIN]) + '_' +
                             str(cls.kwargs[LAT_MAX]) + '_' +
                             str(cls.kwargs[REF_MEAS]) + '_' +
                             str(cls.kwargs[REF_YEAR]) + '_' +
                             str(cls.kwargs[REF_FILLNA]))


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

    def test_get_model_detail_no_email(self):
        """
        Test that model detail does not contain emails
        """
        o3kwargs = {
            'model': self.kwargs[MODELS][0]
        }
        o3model_detail = o3api.get_model_detail(**o3kwargs)
        logger.info(o3model_detail)
        self.assertNotIn(self.fake_email, str(o3model_detail))

    def test_get_dataset_values(self):
        """
        Test that returned dataset values are the same as generated.
        """
        model = self.kwargs[MODELS][-1]
        ds = o3api.o3data['tco3_zm'][model]
        self.assertEqual(ds, self.o3ds)

    def test_get_dataslice_type(self):
        """
        Test that the returned dataset type is correct, xarray.Dataset
        """
        model = self.kwargs[MODELS][0]
        ds = self.rdata.get_dataslice(model)
        self.assertTrue(type(ds) is xr.Dataset)

    def test_check_datasliece_lat(self):
        """
        Test if latitudes are correct for the selected slice
        """
        lat_min = self.kwargs[LAT_MIN]
        lat_max = self.kwargs[LAT_MAX]

        model = self.kwargs[MODELS][0]
        ds = self.rdata.get_dataslice(model)

        lat_0 = np.amin(ds.coords[LAT].values[0]) # min latitude
        lat_last = np.amax(ds.coords[LAT].values[-1]) # max latitude

        self.assertEqual([lat_min, lat_max], [lat_0, lat_last])

    def test_get_data_pd_type(self):
        """
        Test that the returned data type is correct, pd.DataFrame
        """
        model = self.kwargs[MODELS][0]
        ds = self.rdata.get_raw_data_pd(model)
        self.assertTrue(type(ds) is pd.DataFrame)

    def test_get_ensemble_pd_type(self):
        """
        Test that the returned data type is correct, pd.DataFrame
        """
        models = self.kwargs[MODELS]
        ds = self.rdata.get_raw_ensemble_pd(models)
        self.assertTrue(type(ds) is pd.DataFrame)

    def test_get_ref_value(self):
        """
        Test that get_ref_value() is correct
        """
        ref_value, __ = self.pdata.get_ref_value()
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

    def test_get_plot_info_html(self):
        """
        Test setting of the plot info (HTML)
        """
        o3plot_info = phlp.get_plot_info_html(**self.kwargs)
        self.assertIn(cfg.O3AS_LEGALINFO_TXT, o3plot_info)
        self.assertIn(cfg.O3AS_LEGALINFO_URL, o3plot_info)
        self.assertIn(cfg.O3AS_ACKNOWLEDGMENT_TXT, o3plot_info)
        self.assertIn(cfg.O3AS_ACKNOWLEDGMENT_URL, o3plot_info)
        self.assertIn(self.kwargs[PTYPE], o3plot_info)


if __name__ == '__main__':
    unittest.main()
