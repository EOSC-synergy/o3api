# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2020 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under the MIT License
# Please, see the LICENSE file
#
# @author: vykozlov

import logging
import os

# logging level accross various scripts
log_level = logging.DEBUG #INFO # DEBUG # WARNING
 
# identify basedir for the package
O3API_BASE_DIR = os.path.dirname(os.path.normpath(os.path.dirname(__file__)))

# Base path for data
# Default is /srv/o3api/data/
# But one can change using environment $O3AS_DATA_BASEPATH
O3AS_DATA_BASEPATH = os.getenv('O3AS_DATA_BASEPATH', '/srv/o3api/data/')

O3AS_TCO3Return_BOXCAR_WINDOW = 10
O3AS_TCO3Return_BEGIN_YEAR=1970
O3AS_TCO3Return_END_YEAR=2100

# should become obsolete:
O3AS_TCO3_REF_MEAS = os.getenv('O3AS_TCO3_REF_MEAS', 'SBUV_GSFC_merged-SAT-ozone')
O3AS_TCO3_REF_YEAR = os.getenv('O3AS_TCO3_REF_YEAR', 1980)

# list of trusted OIDC providers
trusted_OP_list = [
'https://b2access.eudat.eu/oauth2/',
'https://b2access-integration.fz-juelich.de/oauth2',
'https://unity.helmholtz-data-federation.de/oauth2/',
'https://login.helmholtz-data-federation.de/oauth2/',
'https://login-dev.helmholtz.de/oauth2/',
'https://login.helmholtz.de/oauth2/',
'https://unity.eudat-aai.fz-juelich.de/oauth2/',
'https://services.humanbrainproject.eu/oidc/',
'https://accounts.google.com/',
'https://aai.egi.eu/oidc/',
'https://aai-dev.egi.eu/oidc/',
'https://login.elixir-czech.org/oidc/',
'https://iam-test.indigo-datacloud.eu/',
'https://iam.deep-hybrid-datacloud.eu/',
'https://iam.extreme-datacloud.eu/',
'https://oidc.scc.kit.edu/auth/realms/kit/',
'https://proxy.demo.eduteams.org'
]

# netCDF variable names and coodrinates
netCDF_conf = {
    'tco3'  : 'tco3_zm',
    'tco3_r': 'tco3_return',
    'vmro3' : 'vmro3_zm',
    't_c'   : 'time',
    'lat_c' : 'lat'}

# REST API parameters. See also swagger.yml (!) # TO CHANGE!
api_conf = {
    'plot_t' : 'ptype',
    'models' : 'models',
    'begin'  : 'begin',
    'end'    : 'end',
    'month'  : 'month',
    'lat_min': 'lat_min',
    'lat_max': 'lat_max',
    'ref_meas': 'ref_meas',
    'ref_year': 'ref_year',
}

tco3_return_regions = {
    'Antarctic(Oct)': {'lat_min': -90, 'lat_max': -60, 'month': [10]},
    'SH mid-lat': {'lat_min': -60, 'lat_max': -35, 'month': ''},
    'Tropics': {'lat_min': -20, 'lat_max': 20, 'month': ''},
    'NH mid-lat': {'lat_min': 35, 'lat_max': 60, 'month': ''},
    'Arctic(Mar)': {'lat_min': 60, 'lat_max': 90, 'month': [3]},
    'Near global': {'lat_min': -60, 'lat_max': 60, 'month': ''},
    'Global': {'lat_min': -90, 'lat_max': 90, 'month': ''},
}
# configuration for plotting
# ToDo: use file?
plot_conf = {
    'plot_st' : 'plotstyle',
    netCDF_conf['tco3']: {
        'fig_size': [9, 6],
        'xlabel': 'Year',
        'ylabel': 'Total column Ozone, zonal mean (DU)', #tco3_zm (DU)
        'plotstyle' : { 'color': 'color', 
                        'linestyle': 'linestyle',
                        'linewidth': 'linewidth'}
        },
    netCDF_conf['tco3_r']: {
        'fig_size': [9, 6],
        'xlabel': 'Region',
        'ylabel': 'Return year',
        'plotstyle' : { 'color': 'color', 
                        'linestyle': 'linestyle',
                        'linewidth': 'linewidth',
                        'marker': 'marker'}
        }
}

