import xarray as xr
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose # accurate enough
# from statsmodels.tsa.seasonal import STL # more accurate
import pandas as pd

# The path and the filename need to be input variables:
path = '/home/eo9869/O3as/Output/'
filename = 'era-int_pl_o3_50hPa_zm.nc'
# data analysis:
data = xr.open_dataset(path+filename)
# chose the data to plot (here a mean from +-5 degs of the  equator)
ozone = data.sel(lat=slice(5,-5)).mean(dim=['lat','lon','level']).o3
# result = seasonal_decompose(ozone.values.squeeze(), model='additive', period=365*4)
result = seasonal_decompose(ozone, period=365*4) # maybe good enough because it is much faster
# result = STL(ozone,period=4*365).fit() # more accurate but very slow

# data visualisation:
result.plot()
plt.savefig(path+filename[:-3]+'.pdf', format='pdf')
# plt.show()
plt.close()
