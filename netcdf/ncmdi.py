#!/usr/bin/env python2.7
"""
Display an ascii grid of the number of values in variable varname which are set
to the missing data indicator (MDI). The number of MDI values are reported as a
ceiling power of ten, i.e. 1 for <= 10 MDI values, 2 for <= 100, 3 for <= 1000,
and so on. The specified netcdf variable can be 2, 3 or 4-dimensional.

The optional command-line arguments di and dj define the size of the data block
for which to count MDI values. The default settings of 12 and 6 would result in
counts being generated for each 30 deg x 30 deg block in a 1-degree global grid.
These settings are unlikely to be sensible for most netcdf files!

usage: ncmdi ncfile varname [di [dj]]
"""

import sys
import netCDF4 as nc4
import numpy as np
import numpy.ma as ma
from math import ceil, log10

usage = "usage: ncmdi ncfile varname [di [dj]]"

MAX_COLS_OR_ROWS = 50


def main(ncfile, varname, di, dj):
    ds = nc4.Dataset(ncfile)
    var = ds.variables[varname]
    if var.ndim < 2:
        print >>sys.stderr, "Variable '%s' is not 2-dimensional or higher." % varname
        ds.close()
        sys.exit(1)
    if not ('_FillValue' in var.ncattrs() or 'missing_value' in var.ncattrs()):
        print >>sys.stdout, "Variable '%s' has no missing values." % varname
        ds.close()
        sys.exit(0)

    nrows, ncols = var.shape[-2:]
    jdimname, idimname = var.dimensions[-2:]
    if idimname in ds.variables:
        idim = ds.variables[idimname]
    else:
        idim = range(ncols)
    if jdimname in ds.variables:
        jdim = ds.variables[jdimname]
    else:
        jdim = range(nrows)
    jinc = jdim[0] < jdim[-1]   # True if j axis is monotonic increasing, else False

    if ncols % di != 0:
        print >>sys.stderr, "WARNING: Block length along i axis (%d) is not an integer factor" \
                            " of axis length (%d)." % (di, ncols)
#        ds.close()
#        sys.exit(1)
        ni = ncols/di + 1
    else:
        ni = ncols/di
    if ni > MAX_COLS_OR_ROWS:
        print >>sys.stderr, "Too many blocks (%d) along i axis. Maximum is %d." % (ni, MAX_COLS_OR_ROWS)
        print >>sys.stderr, "Try specifying a larger block length via the di option."
        ds.close()
        sys.exit(1)

    if nrows % dj != 0:
        print >>sys.stderr, "WARNING: Block length along j axis (%d) is not an integer factor" \
                            " of axis length (%d)." % (dj, nrows)
#        ds.close()
#        sys.exit(1)
        nj = nrows/dj + 1
    else:
        nj = nrows/dj
    if nj > MAX_COLS_OR_ROWS:
        print >>sys.stderr, "Too many blocks (%d) along j axis. Maximum is %d." % (nj, MAX_COLS_OR_ROWS)
        print >>sys.stderr, "Try specifying a larger block length via the dj option."
        ds.close()
        sys.exit(1)

    print >>sys.stdout, "MDI grid for variable %s in file %s" % (varname, ncfile)
    print >>sys.stdout, "Block length along i axis (%s): %d cols" % (idimname, di)
    print >>sys.stdout, "Block length along j axis (%s): %d rows" % (jdimname, dj)
    print >>sys.stdout

    total_mdi = 0
    irange = range(0, ncols, di)
    jrange = range(0, nrows, dj)
    if jinc : jrange.reverse()
    for j0 in jrange:
        j1 = j0+dj
        if jinc:
            jcrd = jdim[min(j1-1,nrows-1)]
        else:
            jcrd = jdim[j0]
        mdi_counts = []
        for i0 in irange:
            i1 = i0+di
#            chunk = var[j0:j1,i0:i1]
            chunk = get_2d_data_chunk(var, i0, i1, j0, j1)
            if ma.isMA(chunk):
                nmdi = ma.count_masked(chunk)
            else:
                nmdi = 0
            mdi_counts.append(nmdi)
            total_mdi += nmdi
        print_separator(ni, jcrd)
        print_cells(mdi_counts)

    if jinc:
        print_separator(ni, jdim[0])
    else:
        print_separator(ni, jdim[-1])

    print_iaxis_labels(ni, idim[0], idim[-1])

    print >>sys.stdout, "\nNumbers in grid cells represent maximum number of MDIs as a power of ten"
    print >>sys.stdout, "Actual number of MDIs in a cell could be as low as 10^(n-1)+1"
    print >>sys.stdout, "Total number of MDI values: %d" % total_mdi

    ds.close()


def get_2d_data_chunk(var, i0, i1, j0, j1):
    # not an especially elegant solution, but it'll suffice
    if var.ndim == 2:
        return var[j0:j1,i0:i1]
    elif var.ndim == 3:
        return var[0,j0:j1,i0:i1]
    elif var.ndim == 4:
        return var[0,0,j0:j1,i0:i1]


def print_separator(ni, jcrd=None):
    crdstr = ' ' * 10
    if jcrd is not None:
        crdstr = '%8.3f  ' % jcrd
    sep = '+' + '-+'*ni
    print >>sys.stdout, crdstr+sep


def print_cells(mdi_counts):
    cells = [' '] * len(mdi_counts)
    for i,v in enumerate(mdi_counts):
        if v > 0:
            n = int(ceil(log10(v))) if v > 1 else 1
            cells[i] = str(n)
    pad = ' ' * 10
    sep = '|'
    print >>sys.stdout, pad + sep + sep.join(cells) + sep


def print_iaxis_labels(ni, crd0, crd1):
    lspace = ' ' * 10
    gap = ' ' * (ni*2-1)
    ticks  = lspace + "'" + gap + "'"
    print >>sys.stdout, ticks
    lspace = ' ' * 6
    gaplen = (ni*2-8)
    if gaplen < 1 : gaplen = 1
    gap = ' ' * gaplen
    crd0str = '%8.3f' % crd0
    crd1str = '%8.3f' % crd1
    numbers = lspace + crd0str + gap + crd1str
    print >>sys.stdout, numbers


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print usage
        sys.exit(1)
    ncfile = sys.argv[1]
    varname = sys.argv[2]
    di = 12
    dj = 6
    if len(sys.argv) > 3:
        di = int(sys.argv[3])
        dj = di
    if len(sys.argv) > 4:
        dj = int(sys.argv[4])
    main(ncfile, varname, di, dj)
