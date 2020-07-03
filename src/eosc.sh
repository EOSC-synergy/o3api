#!/usr/bin/env bash
# example for data selection and data reduction 
# by tobias kerzenmacher, 29th may 2020
#
# source data must reside in $inpath
# results are stored in $outpath
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

# Script full path
# https://unix.stackexchange.com/questions/17499/get-path-of-current-script-when-executed-through-a-symlink/17500
SCRIPT_PATH="$(dirname "$(readlink -f "$0")")"

function usage()
{
    shopt -s xpg_echo
    echo "Usage: $0 <options> \n
    Options:
    -h|--help \t\t this help message
    -i|--inpath \t where the source data resides, full path
    -o|--outpath \t where the results will be stored, full path
    -b|--beginyear the start year to process
    -e|--endyear the end year to process
    -l|--level \t level" 1>&2; exit 0;
}

# Define default settings
# define where the source data resides
inpath=/srv/o3as/Data/raw/
# define where the results will be stored
outpath=/srv/o3as/Data/output/
# select the start year
beginyear=1980
#select the end year
endyear=1981
# select the level
level=50

function check_arguments()
{
    OPTIONS=h,i:,o:,b:,e:,l:
    LONGOPTS=help,inpath:,outpath:,beginyear:,endyear:,level:
    # https://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
    # saner programming env: these switches turn some bugs into errors
    set -o errexit -o pipefail -o noclobber -o nounset
    #set  +o nounset
    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        echo '`getopt --test` failed in this environment.'
        exit 1
    fi

    # -use ! and PIPESTATUS to get exit code with errexit set
    # -temporarily store output to be able to check for errors
    # -activate quoting/enhanced mode (e.g. by writing out “--options”)
    # -pass arguments only via   -- "$@"   to separate them correctly
    ! PARSED=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        # e.g. return value is 1
        #  then getopt has complained about wrong arguments to stdout
        exit 2
    fi
    # read getopt’s output this way to handle the quoting right:
    eval set -- "$PARSED"

    if [ "$1" == "--" ]; then
        echo "[INFO] No arguments provided. Start with defaults"
    fi

    # now enjoy the options in order and nicely split until we see --
    while true; do
        case "$1" in
            -h|--help)
                usage
                shift
                ;;
            -i|--inpath)
                inpath="$2"
                shift 2
                ;;
            -o|--outpath)
                outpath="$2"
                shift 2
                ;;
            -b|--beginyear)
                beginyear="$2"
                shift 2
                ;;
            -e|--endyear)
                endyear="$2"
                shift 2
                ;;
            -l|--level)
                level="$2"
                shift 2
                ;;
             *)
                break
                ;;
            esac
        done
}

check_arguments "$0" "$@"

# data reduction: select the ozone variable from the input files at the desired level 
# and calculate the zonal mean (average over all longitudes) of the selected variable
# this could be done in two steps:
file_list=()
for i in $(seq ${beginyear} ${endyear}) ; do file_list+=(${inpath}/era-int_pl_${i}????.nc) ; done
parallel cdo zonmean -selvar,o3 -sellevel,${level} {} ${outpath}{/.}_o3_${level}hPa_zm.nc :::  ${file_list[*]}
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
data_merged=${outpath}era-int_pl_o3_${level}hPa_zm-${beginyear}_${endyear}.nc
cdo -O -b 32 mergetime ${outpath}era-int_pl_????_o3_${level}hPa_zm.nc ${data_merged}
#
# and remove the intermediate yearly files
rm -f ${outpath}era-int_pl_????_o3_${level}hPa_zm.nc
#
# now we can process the results file, e.g. smoothing using a running mean
#
# now we can plot the results file and the processed results file (at the moment all in one file):
python3 "$SCRIPT_PATH/processing.py" --dataset ${data_merged}
#
ls -la $outpath/*pdf
# now we can export the file to a web server
#
# the end
