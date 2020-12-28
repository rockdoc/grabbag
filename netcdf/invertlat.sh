#!/bin/bash
#
# Invert the latitude coordinate, and any dependent variables, in a netCDF file.
# By default this script looks for a latitude variable named 'lat', a latitude bounds
# variable named 'lat_bnds', and a bounds dimension named 'bnds'. These defaults may
# be overridden using the -l, -b and -d options, respectively. If there is no bounds
# variable, then set -b to the empty string using the following command invocation:
#
# $ invertlat.sh -b '' infile outfile
#
# This script assumes that the specified latitude variable has a dimension with the
# same name (i.e. it's a CF coordinate variable).
#
# PLEASE NOTE: outfile is overwritten if it exists.

print_usage () {
   echo "usage: invertlat.sh [-b bnds_var] [-d bnds_dim] [-l lat_var] infile outfile"
}

# check for correct number of arguments
if [ $# -lt 2 ]; then
   print_usage
   exit 1
fi
invocation="`date`: invertlat.sh $*"

# set default command-line options
options=":b:d:l:"
latvar="lat"
latdim=$latvar
bndvar="lat_bnds"
bnddim="bnds"

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
      d) bnddim=$OPTARG ;;
      l) latvar=$OPTARG ;;
      *) echo "Unknown option: $OPTARG" ;
         exit 1 ;;
   esac
done

# get the input and output netcdf filenames
shift $(($#-2))
infile=$1
outfile=$2

echo "Inverting latitude dimension $latdim..."
ncpdq -h -O -a -$latdim $infile $outfile

if [ -n "$bndvar" ]; then
    echo "Inverting bounds dimension for variable $bndvar..."
    tmpfile="${bndvar}_pid_$$.tmp"
    ncpdq -h -O -a -$bnddim -v $bndvar $outfile $tmpfile

    echo "Replacing bounds variable in output file..."
    ncks -h -A -v $bndvar $tmpfile $outfile
    rm $tmpfile
fi

echo "Updating history attribute..."
ncatted -h -a history,global,a,c,"$invocation" $outfile

echo "All done."
exit 0
