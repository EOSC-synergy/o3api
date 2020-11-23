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
log_level = logging.DEBUG

# Base path for data
# Default is /srv/o3api/data/
# But one can change using environment $O3AS_DATA_BASEPATH
O3AS_DATA_BASEPATH = os.getenv('O3AS_DATA_BASEPATH', "/srv/o3api/data/")

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

# configuration for plotting
# ToDo: use file?
plot_conf = {
    'plot_t': 'type',
    'time_c': 'time',
    'tco3_zm': {
        'fig_size': [9, 6],
        'inputs' : ['begin_year', 'end_year', 'lat_min', 'lat_max']
        }
}

