# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019 Karlsruhe Institute of Technology - Steinbuch Centre for Computing
# This code is distributed under its License. Please, see the LICENSE file
#
# @author: vykozlov

import argparse
import glob
import logging
import numpy as np
import os
import pandas as pd
import time
import xarray as xr

logger = logging.getLogger('__name__') #o3asplot
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
    
    model_path_out = os.path.join(data_path_out, model)
    if not os.path.exists(model_path_out):
        os.makedirs(model_path_out, exist_ok=True)

    if (args.single_file):
        path = os.path.join(data_path_out, model, 
                            "%s_%s.nc" % ('tco3_zm', 
                                           model))
        ds.to_netcdf(path, format='NETCDF4')
    else:
        years, datasets_yearly = zip(*ds.groupby("time.year"))
        decades = [ (y//10)*10 for y in years ]
        print(F"[DEBUG, Years]: {years}")
        print(F"[DEBUG, Decades]: {decades}")

        print("Element 0:")
        print(years[0], datasets_yearly[0])

        start_for = time.time()
        max_years = len(decades)
        ds_10y = [datasets_yearly[0]]
        for i in range(1, max_years):
            if decades[i] == decades[i-1]:
                ds_10y.append(datasets_yearly[i])
            else:
                path = os.path.join(data_path_out, model, 
                                    "%s_%s.nc" % ('tco3_zm', decades[i-1]))
                print(F"[INFO] NEW DATASET. PATH: {path}")
                dataset_10y = xr.concat(ds_10y, 'time')
                dataset_10y.to_netcdf(path, format='NETCDF4')
                ds_10y = [datasets_yearly[i]]

        print(F"Time for the loop: {time.time() - start_for}")


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
    parser.add_argument('--single_file', type=bool, default=False, help='Store dataset in one file')
    args = parser.parse_args()

    main()
