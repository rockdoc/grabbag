#!/usr/bin/env python2.7
"""
Computes and prints the RMS error between the variable named var1 in netcdf file1
and variable var2 in netcdf file2. If var2 isn't specified then it defaults to var1.
This script assumes that the data arrays associated with var1 and var2 either have
the same shape or else are broadcastable, one to the other.
"""

import sys
import netCDF4 as nc4
import numpy as np
import numpy.ma as ma

usage = "Usage: ncrmse file1 file2 var1 [var2]"


def main():
    if len(sys.argv) < 4:
        print usage
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    varname1 = sys.argv[3]
    try:
        varname2 = sys.argv[4]
    except:
        varname2 = varname1

    try:
        ds1 = nc4.Dataset(file1, 'r')
        ds2 = nc4.Dataset(file2, 'r')
        var1 = ds1.variables[varname1]
        var2 = ds2.variables[varname2]
        rmse = rmserror(var1[:], var2[:])
        print >>sys.stdout, rmse
        retcode = 0
    except KeyError:
        print >>sys.stderr, "ERROR: One or both of the specified variable names is invalid."
        retcode = 1
    except ValueError:
        print >>sys.stderr, "ERROR: Problem trying to compute RMS error. Check input files contain valid data."
        retcode = 1
    finally:
        ds1.close()
        ds2.close()

    sys.exit(retcode)


def rmserror(arr1, arr2):
    """Compute RMS error."""
    if ma.isMA(arr1) and np.all(arr1.mask):
        raise ValueError("First array argument contains all masked values.")
    if ma.isMA(arr2) and np.all(arr2.mask):
        raise ValueError("Second array argument contains all masked values.")
    return ma.sqrt( ((arr1-arr2)**2).mean(dtype='float64') )


if __name__ == "__main__":
    main()
