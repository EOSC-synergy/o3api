# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under its License. Please, see the LICENSE file
#
# @author: vykozlov

import argparse
import glob
import logging
import os
import time
import xarray as xr

logger = logging.getLogger('__name__') #o3api
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
logger.setLevel(logging.DEBUG)


def main():

    data_path = args.data_path
    model = args.model
    data_pattern = "%s*.nc" % (args.pattern)
    data_path_out = args.data_path_out

    data_files = glob.glob(os.path.join(data_path, 
                                        model, 
                                        data_pattern))

    ds = xr.open_mfdataset(data_files, 
                           #chunks={'latitude': 96, 'longitude': 96},
                           concat_dim="time",
                           data_vars='minimal', coords='minimal',
                           parallel=False)
                           
    print(F"Dataset: {ds}")
    try:
        min_year = ds.coords['time'].values[0].year
    except AttributeError:
        min_year = ds.indexes['time'].year[0]
    print(F"Dataset time coords: {min_year}")
    try:
        max_year = ds.coords['time'].values[-1].year
    except AttributeError:
        max_year = ds.indexes['time'].year[-1]
    print(F"Dataset time coords: {max_year}")
    #print(F"Dataset time: {ds['time'].values}")
    print(type(ds.time))
    print(ds.time)
    print(type(ds.time.values))
    print(ds.time.values)
    try:
        ds = ds.assign(decade=((ds.coords['time'].values.to_datetimeindex().year//10)*10))
    except AttributeError:
        ds = ds.assign_coords(decade=((ds.indexes['time'].to_datetimeindex().year//10)*10))

    print(F"New Dataset: {ds}")

    model_path_out = os.path.join(data_path_out, model)
    if not os.path.exists(model_path_out):
        os.makedirs(model_path_out, exist_ok=True)

    years, ds_grouped = zip(*ds.groupby("decade")) #.year//10)*10
    #print(F"Datasets: {ds_grouped}")
    decades = [ (y//10)*10 for y in years ]
    datasets = ds_grouped
    datasets = [ ds.drop_dims('decade') for ds in ds_grouped ]
    paths = [os.path.join(data_path_out, model, "%s_%s.nc" % 
                         ('tco3_zm', y)) for y in years]
    xr.save_mfdataset(datasets, paths) # store only tco3_zm values


if __name__ == '__main__':

    # Define script parameters:
    parser = argparse.ArgumentParser(description='Script parameters')
    parser.add_argument('--data_path', type=str, default='data/',
                        help='Path for the data (default: data/)')
    parser.add_argument('--model', type=str, default='CCMI-1_ACCESS-refC2',
                        help='Model data to combine (default: CCMI-1_ACCESS-refC2)')
    parser.add_argument('--pattern', type=str, default='tco3_zm',
                        help='Pattern to select files (default: tco3_zm)')
    parser.add_argument('--data_path_out', type=str, default='data/combined',
                        help='Path for the combined data (default: data/combined)')
    args = parser.parse_args()

    main()
