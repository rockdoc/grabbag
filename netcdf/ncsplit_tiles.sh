#!/bin/bash
#
# Split a netcdf file into a series of rectangular tile files. The tile size is defined in terms of
# x and y dimension indices, where the x dimension is typically longitude, and the y dimension is
# is typically latitude, though this is not obligatory.
#
# Output files are generated in row-major order and are named according to to the convention
# <basename>_tile<n>.nc, where n is the tile number (1-based by default, but can be altered using
# the starttilenum argument.
#
# This script requires the NCO and ncdump utilities to be on the user's command search path.

usage="usage: ncsplit_tiles.sh file xdim xtilesize ydim ytilesize [starttilenum=1]"
if [ $# -lt 5 ]; then
    echo $usage
    exit 1
fi

# Define a whitespace class comprising the space and tab characters.
tab=$'\t'
ws="[ $tab]"

# Read command-line arguments.
ncfile=$1
xdim=$2
xtilesize=$3
ydim=$4
ytilesize=$5
starttilenum=${6:-1}
stride=1

# Get dimension lengths
xdimlen=`ncdump -h ${ncfile} | egrep "^${ws}+${xdim}${ws}*=.*" | sed 's/ *\;$//' | cut -d ' ' -f 3`
ydimlen=`ncdump -h ${ncfile} | egrep "^${ws}+${ydim}${ws}*=.*" | sed 's/ *\;$//' | cut -d ' ' -f 3`

# Calculate number of tiles along the x and y dimensions.
let nx=xdimlen/xtilesize
if [ $((nx*xtilesize)) -lt $xdimlen ]; then let nx++; fi
let ny=ydimlen/ytilesize
if [ $((ny*ytilesize)) -lt $ydimlen ]; then let ny++; fi
let ntiles=ny*nx

# Set basename of output files.
#opfilebase=`basename $ncfile .nc`
opfilebase=${ncfile%.*}

# Ask user to confirm operation
dryrun=0
echo "The specified tilesizes will result in $ntiles tiles ($ny rows x $nx cols)"
read -p "Continue? (y=yes, n=no, d=dry-run): " reply
if [ "$reply" == "n" ]; then
    exit;
elif [ "$reply" == "d" ]; then
    echo "*** Dry-run only; no tiles will be created ***"
    dryrun=1;
fi

# Define chunking options.
#chunking_options="--cnk_plc=g2d --cnk_dmn ${ydim},1024 --cnk_dmn ${xdim},1024"

# Loop over rows and columns, writing each tile of data to a new file.
for ((j=0; j<$ny; j+=1)); do
    let j0=j*ytilesize
    let j1=j0+ytilesize-1
    if [ $j1 -ge $ydimlen ]; then let j1=ydimlen-1; fi
    for ((i=0; i<$nx; i+=1)); do
        let i0=i*xtilesize
        let i1=i0+xtilesize-1
        if [ $i1 -ge $xdimlen ]; then let i1=xdimlen-1; fi
        let tileno=i+j*$nx+$starttilenum
        tileno=`printf "%0${#ntiles}d" $tileno`
        opfile=${opfilebase}_tile${tileno}.nc
        cmd="ncks -O -d ${ydim},${j0},${j1} -d ${xdim},${i0},${i1} ${ncfile} ${opfile}"
        echo "Running $cmd"
        if [ $dryrun -ne 1 ]; then
            $cmd
        fi
    done
done

echo "Task completed."
exit 0
