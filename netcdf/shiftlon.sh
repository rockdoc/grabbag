#!/bin/bash
#
# Shift netcdf data in longitude range (-180 <= lon < 0) to range (180 <= lon < 360)
# By default the script looks for a longitude variable called 'lon' and a longitude
# bounds variable called 'lon_bnds'. These defaults may be overridden using the -l
# and -b options. If there is no bounds variable, set -b to the empty string using
#    shiftlon.sh -b '' infile outfile
#
# The -r option may be used to apply the reverse longitude shift, i.e. from range
# (180 < lon <= 360) to range (-180 < lon <= 0).
#
# This script should exhibit reasonable performance for small to medium size files.
# For large-ish files (> 500 MB) it may be necessary to seek an alternative solution
# or else split the input file into a series of smaller files.

print_usage () {
   echo "usage: shiftlon.sh [-b bnds_var] [-l lon_var] [-r] infile outfile"
}

# check for correct number of arguments
if [ $# -lt 2 ]; then
   print_usage
   exit 1
fi

# set default command-line options
options=":b:l:r"
lonvar="lon"
bndvar="lon_bnds"
reverse=0

# parse command-line options
while true
do
   getopts $options opt
   if [ $? -ne 0 ]; then
      break
   fi
   case $opt in
      \?) print_usage ;
         exit 0 ;;
      b) bndvar=$OPTARG ;;
      l) lonvar=$OPTARG ;;
      r) reverse=1 ;;
      *) echo "unknown option: $OPTARG" ;
         exit 1 ;;
   esac
done

# get the input and output netcdf filenames
shift $(($#-2))
infile=$1
outfile=$2

# reorder the data from |west|east| to |east|west| i.e. -180 -> 180 to 0 -> 360
if [ $reverse -eq 0 ]; then
    echo "Shifting longitudes from (-180 -> 180) to (0 -> 360)"
    ncks -O -d ${lonvar},0.,180. -d ${lonvar},-180.,-0.001 --msa $infile $outfile

    # build and execute an ncap2 script to adjust the longitude values
    #ncap2 -O -s 'where(lon<0) lon_bnds=lon_bnds+360; where(lon<0) lon=lon+360' $outfile $outfile
    script="where(${lonvar}<0) ${lonvar}=${lonvar}+360"
    if [ -n "$bndvar" ]; then
        script="where(${lonvar}<0) ${bndvar}=${bndvar}+360; $script"
    fi
    ncap2 -O -s "$script" $outfile $outfile

# reorder the data from |east|west| to |west|east| i.e. 0 -> 360 to -180 -> 180
else
    echo "Shifting longitudes from (0 -> 360) to (-180 -> 180)"
    ncks -O -d ${lonvar},180.0001,360. -d ${lonvar},0.,180. --msa $infile $outfile

    # build and execute an ncap2 script to adjust the longitude values
    script="where(${lonvar}>180) ${lonvar}=${lonvar}-360"
    if [ -n "$bndvar" ]; then
        script="where(${lonvar}>180) ${bndvar}=${bndvar}-360; $script"
    fi
    ncap2 -O -s "$script" $outfile $outfile

fi

echo "All done."
exit 0
