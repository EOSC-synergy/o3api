import xarray as xr
import matplotlib.pyplot as plt


if __name__ == "__main__":
    data = xr.open_dataset('./Data/era5_ozone_mass_mixing_ratio_zm_30.nc')
    data.o3.T.plot(robust=True)
    plt.show()
