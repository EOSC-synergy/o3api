#!/bin/bash
# example for data selection and data reduction 
# by tobias kerzenmacher, 29th may 2020
#
# source data must reside in $inpath
# results are stored in $oupath
#
# data model: var(longitude,latitude,level,time)
# var: variable (e.g. ozone mixing ratio)
# longitude, latitude: index for geolocation
# level: index for pressure / altitude (e.g. hPa)
# time: index for time (e.g. hours since start time - 6 hourly spacing)
#
# the script uses "parallel" (https://www.gnu.org/software/parallel/)
# and "cdo" (https://code.mpimet.mpg.de/projects/cdo)
# to extract ozone 
# on $level (in hPa) and takes the zonal mean (average over all longitudes)
# result files are merged in a two-step approach
# avoiding memory issues while creating the time series in $outpath
#
export PATH=$PATH:/home/px5501/bin
# define where the source data resides
inpath=/home/px5501/O3as/Data/Ecmwf/
# define where the results will be stored
outpath=$HOME/O3as/Output/
# select the level
level=50
# select the start year
beginyear=1980
#select the end year
endyear=1981
#
# data reduction: select the ozone variable from the input files at the desired level 
# and calculate the zonal mean (average over all longitudes) of the selected variable
# this could be done in two steps:
parallel cdo zonmean -selvar,o3 -sellevel,${level} {} ${outpath}{/.}_o3_${level}hPa_zm.nc :::  ${inpath}/era-int_pl_198[0-1]????.nc
#
# 'cdo mergetime' does produce a memory timeout if all the files are merged at once, 
# thus first merge all the data from one year:
for i in $(seq ${beginyear} ${endyear}) ; do cdo -b 32 mergetime ${outpath}era-int_pl_${i}????_o3_${level}hPa_zm.nc ${outpath}era-int_pl_${i}_o3_${level}hPa_zm.nc ; done
#for i in {${beginyear}..${endyear}} ; do cdo -b 32 mergetime ${outpath}era-int_pl_${i}????_o3_${level}hPa_zm.nc ${outpath}era-int_pl_${i}_o3_${level}hPa_zm.nc ; done
#
# clear some space by removing intermediate files:
rm -f ${outpath}era-int_pl_????????_o3_${level}hPa_zm.nc
#
# now merge the files of the individual years:
cdo -O -b 32 mergetime ${outpath}era-int_pl_????_o3_${level}hPa_zm.nc ${outpath}era-int_pl_o3_${level}hPa_zm.nc
#
# and remove the intermediate yearly files
rm -f ${outpath}era-int_pl_????_o3_${level}hPa_zm.nc
#
# now we can process the results file, e.g. smoothing using a running mean
#
# now we can plot the results file and the processed results file (at the moment all in one file):
source /home/px5501/.venv/O3as/bin/activate
python3 $HOME/O3as/Scripts/processing.py
deactivate
#
evince $outpath/*pdf
# now we can export the file to a web server
#
# the end
