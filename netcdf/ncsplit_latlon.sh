#!/bin/bash
#
# Split a netcdf file into a series of latitude-longitude tile files.
# Tile sizes are specified as number of rows or columns, rather than degrees.
# Output files are generated in row-major order.
#
# This script requires the NCO and ncdump utilities to be on the user's command search path.

usage="usage: ncsplit_latlon.sh file latdim lattilesize londim lontilesize [starttilenum=1]"

if [[ $# -lt 5 ]]; then
    echo $usage
    exit 1
fi

# Get command arguments.
ncfile=$1
latdim=$2
lattilesize=$3
londim=$4
lontilesize=$5
starttilenum=${6:-1}
stride=1

# Get dimension lengths
latdimlen=`ncdump -h ${ncfile} | egrep "^\s+${latdim}+\s*=.*" | sed 's/ *\;$//' | cut -d ' ' -f 3`
londimlen=`ncdump -h ${ncfile} | egrep "^\s+${londim}+\s*=.*" | sed 's/ *\;$//' | cut -d ' ' -f 3`

# Calculate number of rows, nj, and number of columns, ni.
let nj=latdimlen/lattilesize
let ni=londimlen/lontilesize
let ntiles=nj*ni

# Set basename of output files.
#ncbasename=`basename $ncfile .nc`
opfilebase=${ncfile%.*}

# Ask user to confirm operation
echo "The specified tilesizes will result in $ntiles tiles ($nj rows x $ni cols)"
read -p "Continue? (y/n) " reply
if [ "$reply" != "y" ]; then
    exit
fi

# Define chunking options.
#chunking_options="--cnk_plc=g2d --cnk_dmn ${latdim},1024 --cnk_dmn ${londim},1024"

# Loop over rows and columns, writing each tile of data to a new file.
for ((j=0; j<$nj; j+=1)); do
    let j0=j*lattilesize
    let j1=j0+lattilesize-1
    for ((i=0; i<$ni; i+=1)); do
        let i0=i*lontilesize
        let i1=i0+lontilesize-1
        let tileno=i+j*$ni+$starttilenum
        opfile=${opfilebase}_tile${tileno}.nc
        cmd="ncks -d ${latdim},${j0},${j1},${stride} -d ${londim},${i0},${i1},${stride} ${ncfile} ${opfile}"
        echo "Executing $cmd..."
        $cmd
    done
done

echo "Task completed."
exit 0
