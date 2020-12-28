#!/usr/bin/env python2.7
"""
Reports the spatial extent of a netCDF file. The spatial extent is determined
by scanning the file for representative coordinate variables. By default these
are the variables named 'lon' and 'lat', or 'longitude' and 'latitude'.
Alternatively the variables can be specified via the optional command line
arguments. Any number of coordinate variables may be specified, though the
typical scenario will be to report on two orthogonal horizontal coordinates,
e.g. lat,long or X,Y.
"""
import sys
import os
import netCDF4 as nc4

usage = "Usage: %s ncfile [coord_var [,coord_var] ...]" % os.path.basename(sys.argv[0])

# List of candidate variable names to search for.
candidate_namelists = [
    ['lon', 'lat'],
    ['longitude', 'latitude'],
    ['x', 'y']
]

# String formats for header and variable lines.
hdrfmt = "{0:>16} {1:>12} {2:>12} {3:>8}"
repfmt = "{0:>16} {1:12.4f} {2:12.4f} {3:8d}"


def main():
    ncfile = sys.argv[1]
    ds = nc4.Dataset(ncfile)
    ds_varnames = set([str(x) for x in ds.variables.keys()])

    try:
        coord_vars = None
        if len(sys.argv) > 2:
            coord_vars = sys.argv[2:]
            if not set(coord_vars) <= ds_varnames:
                raise ValueError("Specified coordinate variables not found in file.")
        else:
            for namelist in candidate_namelists:
                if set(namelist) <= ds_varnames:
                    coord_vars = namelist
                    break
            if not coord_vars:
                raise ValueError("No recognised coordinate variables found in file.")

        print "Spatial extent of file", ncfile
        print ""
        print hdrfmt.format('variable', 'start', 'end', 'len')
        print hdrfmt.format('--------', '-----', '---', '---')

        for cvname in coord_vars:
            cv = ds.variables[cvname]
            cvdata = cv[:]
            print repfmt.format(cvname, cvdata[0], cvdata[-1], cv.shape[0])
            check_bounds(ds, cv)
            print

    except:
        print sys.exc_info()[1]
    finally:
        ds.close()


def check_bounds(dataset, var):
    if 'bounds' in var.ncattrs():
        bvname = var.bounds
        bv = dataset.variables[bvname]
        bvdata = bv[:]
        print repfmt.format(bvname, bvdata[0,0], bvdata[-1,1], bv.shape[0])


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print usage
        sys.exit(1)
    main()
