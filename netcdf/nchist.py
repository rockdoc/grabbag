#!/usr/bin/env python2.7
"""
Diplay the global history attribute, if present, for a netcdf file in a legible manner. By default,
separate entries in the history text (i.e. as delimited by newline characters) are displayed in the
order in which they appear, which usually means most recent first. The -r option may be used to
display history lines in reverse order, i.e. oldest first. The -v option results in history attr-
ibutes attached to variables being reported in addition to the global history attribute.

"""
import sys
import os
import netCDF4 as nc4

usage = "Usage: %s ncfile" % os.path.basename(sys.argv[0])


def main():
    options, ncfile = parse_args()
    ds = None
    try:
        ds = nc4.Dataset(ncfile)
        targets = [('',ds)]
        if options.incvars : targets.extend(ds.variables.items())
        nh = 0
        for name, target in targets:
            if 'history' in target.ncattrs():
                print_history(name, target.history, options.reverse)
                nh += 1
        if not nh:
            print "NetCDF file does not contain any history attributes."
    finally:
        if ds is not None : ds.close()


def print_history(name, history, reverse=False):
    if isinstance(history, basestring) : history = history.split('\n')
    if reverse and len(history) > 1 : history.reverse()
    print
    if name:
        varname = "variable: " + name
        print "{0}\n{1}".format(varname, '-'*len(varname))
    for i, line in enumerate(history):
        print "[{0:02d}]  {1}".format(i+1, line)


def parse_args():
    """Parse command-line options and arguments"""
    import optparse

    usage = "usage: %prog [options] ncfile"
    parser = optparse.OptionParser(usage=usage, version="0.1")
    parser.add_option("-r", dest="reverse", action="store_true",
        help="display history lines in reverse order (which usually means oldest first)")
    parser.add_option("-v", dest="incvars", action="store_true",
        help="report history attributes attached to variables as well")

    options, args = parser.parse_args()
    if len(args) < 1 : parser.error("Insufficient arguments specified.")

    ncfile = args[0]
    if not os.path.exists(ncfile):
        parser.error("File {0} does not exist.".format(ncfile))

    return (options, ncfile)


if __name__ == "__main__":
    main()
