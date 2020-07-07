import argparse
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
from os import path
from statsmodels.tsa.seasonal import seasonal_decompose # accurate enough
# from statsmodels.tsa.seasonal import STL # more accurate

def main():
    data_path, data_file = path.split(args.dataset)
    # data analysis:
    data = xr.open_dataset(args.dataset)
    # chose the data to plot (here a mean from +-5 degs of the  equator)
    ozone = data.sel(lat=slice(5,-5)).mean(dim=['lat','lon','level']).o3
    # result = seasonal_decompose(ozone.values.squeeze(), model='additive', period=365*4)
    result = seasonal_decompose(ozone, period=365*4) # maybe good enough because it is much faster
    # result = STL(ozone,period=4*365).fit() # more accurate but very slow

    # data visualisation:
    result.plot()
    figure_file = path.splitext(data_file)[0] + '.pdf'
    plt.savefig(path.join(data_path, figure_file), format='pdf')
    # plt.show()
    plt.close()


if __name__ == '__main__':

    # Define script parameters:
    parser = argparse.ArgumentParser(description='Script parameters')
    parser.add_argument('--dataset', type=str, default='/srv/o3as/output/era-int_pl_o3_50hPa_zm.nc',
                        help='Full path to the dataset file. Default is \
                             /srv/o3as/output/era-int_pl_o3_50hPa_zm.nc')
    args = parser.parse_args()
    
    main()
