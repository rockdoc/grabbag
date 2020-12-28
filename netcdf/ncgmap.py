#!/usr/bin/env python2.7
"""
View, add, update, or delete grid mapping constructs within a CF-compliant netCDF file.

USAGE

ncgmap subcommand [options] [ncfile]

SUBCOMMANDS

list: List the grid mappings defined in ncfile
    ncgmap list [options] <ncfile>

gmlist: Print the recognised CF grid mapping names
    ncgmap gmlist

add: Add a new grid mapping definition to ncfile
    ncgmap add --gmname <gmname> [--gmvname <varname>] <ncfile>

delete: Delete a grid mapping definition and update any data variables that reference it
    ncgmap delete --gmname <gmname> <ncfile>
    ncgmap delete --gmvname <varname> <ncfile>

link: Link (associate) a grid mapping definition with one or more data variables
    ncgmap link --gmname <gmname> -v|--vars <vars> <ncfile>
    ncgmap link --gmvname <varname> -v|--vars <vars> <ncfile>

unlink: Unlink (disassociate) the current grid mapping definition from one or more data variables
    ncgmap unlink -v|--vars <vars> <ncfile>

rename: Rename a grid mapping variable and update any data variables that reference it
    ncgmap rename --gmname <gmname> --gmvname <varname> <ncfile>

OPTIONS

--gmname
    Specify the name of a recognised CF grid mapping, e.g. 'latitude_longitude'.

--gmvname
    Specify the name of the netCDF variable which contains or, for add and rename operations,
    will contain, a grid mapping definition.

--propfile
    The pathname of a text file containing grid mapping properties as space-delimited key-value
    pairs. These properties are attached as netCDF attributes to the grid mapping variable.

-v,--vars
    The names of one or more netCDF data variables to link (associate) or unlink (dissociate)
    with a grid mapping definition.
"""

import os
import sys
import netCDF4 as nc4

# CF version understood by this script.
CF_VERSION = "1.6"

# List of recognised CF grid mapping names (as of CF_VERSION)
CF_GRID_MAPPING_NAMES = [
    'albers_conical_equal_area',
    'azimuthal_equidistant',
    'lambert_azimuthal_equal_area',
    'lambert_conformal_conic',
    'lambert_cylindrical_equal_area',
    'latitude_longitude',
    'mercator',
    'orthographic',
    'polar_stereographic',
    'rotated_latitude_longitude',
    'stereographic',
    'transverse_mercator',
    'vertical_perspective',
]

# Assign default option values.
opt_defaults = {
    'cdl': '',
    'gmname': '',
    'gmvname': '',
    'gmvtype': 'i',
    'propfile': '',
    'vars': '',
    'verbose': False
}


def main():
    """Main control function"""

    # Parse command-line options
    options, subcommand, ncfile = parse_args()

    # If GM name was specified, check that it's valid.
    if options.gmname and not is_valid_gmname(options.gmname):
        print >>sys.stderr, "Invalid grid mapping name:", options.gmname
        sys.exit(1)

    # Invoke the selected subcommand.
    try:
        if subcommand == 'add':
            add(ncfile, options)
        elif subcommand == 'delete':
            delete(ncfile, options)
        elif subcommand == 'gmlist':
            listcfgm()
        elif subcommand == 'link':
            link(ncfile, options)
        elif subcommand == 'list':
            listgm(ncfile, options)
        elif subcommand == 'rename':
            rename(ncfile, options)
        elif subcommand == 'unlink':
            unlink(ncfile, options)
        else:
            print >>sys.stderr, "Unrecognised subcommand:", subcommand

    except Exception, exc:
        print >>sys.stderr, str(exc)


def parse_args():
    """Parse command-line options and arguments"""
    import optparse

    usage = "usage: %prog subcommand [options] [ncfile]"
    parser = optparse.OptionParser(usage=usage, version="0.2")
    parser.set_defaults(**opt_defaults)
    parser.add_option("--doc", dest="doc", action="store_true",
        help="show documentation")
    parser.add_option("--gmname", dest="gmname",
        help="name of a recognised CF grid mapping")
    parser.add_option("--gmvname", dest="gmvname",
        help="name of netcdf variable to use for a grid mapping")
    parser.add_option("--propfile", dest="propfile",
        help="name of text file containing grid mapping property key-value pairs (space-delimited")
    parser.add_option("-v", "--vars", dest="vars",
        help="list of netcdf data variable names to operate on")
    parser.add_option("-V", "--verbose", dest="verbose", action="store_true",
        help="turn on verbose output")

    (options, args) = parser.parse_args()
    if options.doc:
        print __doc__
        sys.exit(0)
    if len(args) < 1: parser.error("Insufficient arguments specified.")

    subcommand = args[0].lower()
    ncfile = '' if len(args) < 2 else args[1]
    options.ncfile = ncfile   # temporary kludge

    return (options, subcommand, ncfile)


def add(ncfile, options):
    """Add a new grid mapping definition to the input file."""

    if not options.gmname:
        print >>sys.stderr, "No grid mapping name specified via the --gmname option."
        return

    # Open a handle on the netcdf file.
    ncdataset = nc4.Dataset(ncfile, 'a')

    gmname = options.gmname
    gmvars = find_grid_mapping_vars(ncdataset)
    if gmname in [v.grid_mapping_name for n,v in gmvars]:
        print "Warning: a grid mapping with name '{0}' is already present in the input file.".format(gmname)
        ncdataset.close()
        return

    if options.gmvname:
        gmvname = options.gmvname
    else:
        gmvname = gmname

    gmvar = ncdataset.createVariable(gmvname, options.gmvtype)
    gmvar.grid_mapping_name = gmname
    print "Added grid mapping with name '{0}' to variable '{1}'".format(gmname, gmvname)

    # Load GM properties from text file, if one was specified via --propfile option.
    if options.propfile:
        try:
            propdict = read_prop_file(options.propfile)
            for k,v in propdict.items():
                gmvar.setncattr(k, v)
                print "Added grid mapping attribute {0} with value {1}".format(k, v)
        except:
            print "Warning: problem trying to read properties from file " + options.propfile

    # If -v/--vars option specified then link data variables to new grid mapping.
    if options.vars:
        for varname in options.vars.split(','):
            try:
                var = ncdataset.variables[varname]
                var.grid_mapping = gmvname
                print "Linked new grid mapping to data variable {0}".format(varname)
            except:
                print "Requested variable called {0} not found - skipping".format(varname)
                continue

    # Close the netcdf file.
    ncdataset.close()


def delete(ncfile, options):
    """Delete a grid mapping definition and update any data variables that reference it."""

    # Open a handle on the netcdf file.
    ncdataset = nc4.Dataset(ncfile, 'a')

    opts_ok = True
    if options.gmname:
        gmname = options.gmname
        gmvname, var = get_grid_mapping_var(ncdataset, gmname)
        if not gmvname:
            print >>sys.stderr, "No grid mapping called {0} was found in the input file.".format(gmname)
            opts_ok = False
    elif options.gmvname:
        gmvname = options.gmvname
    else:
        print >>sys.stderr, "No grid mapping specified via either the --gmname or --gmvname option."
        opts_ok = False

    if not opts_ok:
        ncdataset.close()
        return

    # Update the grid_mapping attribute for any variables that reference the to-be-deleted variable.
    for name, var in ncdataset.variables.items():
        if getattr(var, 'grid_mapping', '') == gmvname:
            del var.grid_mapping
            print "Unlinked grid mapping {0} from data variable {1}".format(gmvname, name)

    # FIXME: Ideally we'd like to delete the GM variable here. However, the netCDF4 module does
    # not currently support deletion of variables. So we'll have to call out to ncks.

    # Close the netcdf file.
    ncdataset.close()

    cmd = "ncks -h -O -x -v {0} {1} {2}".format(gmvname, ncfile, ncfile)
    result = os.system(cmd)
    if result == 0:
        print "Grid mapping variable {0} deleted from input file".format(gmvname)
    else:
        print >>sys.stderr, "Problem trying to delete grid mapping variable {0}".format(gmvname)


def link(ncfile, options):
    """Link a grid mapping with one or more data variables."""

    # Open a handle on the netcdf file.
    ncdataset = nc4.Dataset(ncfile, 'a')

    opts_ok = True
    if options.gmname:
        gmname = options.gmname
        gmvname, var = get_grid_mapping_var(ncdataset, gmname)
        if not gmvname:
            print >>sys.stderr, "No grid mapping called {0} was found in the input file.".format(gmname)
            opts_ok = False
    elif options.gmvname:
        gmvname = options.gmvname
        gmvar = ncdataset.variables[options.gmvname]
        gmname = gmvar.grid_mapping_name
    else:
        print >>sys.stderr, "No grid mapping specified via either the --gmname or --gmvname option."
        opts_ok = False

    # Next check that one or more target variables (for linking to) were specified.
    if not options.vars:
        print >>sys.stderr, "No target data variable(s) specified via the -v/--vars option."
        opts_ok = False

    if not opts_ok:
        ncdataset.close()
        return

    for varname in options.vars.split(','):
        try:
            var = ncdataset.variables[varname]
            var.grid_mapping = gmvname
            print "Linked selected grid mapping to data variable {0}".format(varname)
        except:
            print "Requested variable called {0} not found - skipping".format(varname)
            continue

    # Close the netcdf file.
    ncdataset.close()


def listcfgm():
    """Print a list of recognised CF grid mapping names"""

    print
    print "Recognised CF grid mapping names"
    print "--------------------------------"
    for gm in CF_GRID_MAPPING_NAMES:
        print gm
    print


def listgm(ncfile, options):
    """Print a list of the grid mappings defined in the input file."""

    # Open a handle on the netcdf file.
    ncdataset = nc4.Dataset(ncfile, 'r')

    gmvars = find_grid_mapping_vars(ncdataset)
    if not gmvars:
        print "Input file appears to contain no CF-style grid mapping variables."
        ncdataset.close()
        return

    gmvarnames = [n for n,_ in gmvars]
    gmvardict = {}

    print
    print "Grid mapping definitions"
    print "------------------------"
    for name, var in gmvars:
        print "{0} (defined in variable {1})".format(var.grid_mapping_name, name)
        gmvardict[name] = var.grid_mapping_name
        if options.verbose:
            for attname in var.ncattrs():
                print "\t{0} = {1}".format(attname, var.getncattr(attname))
        print

    print "Grid mapping associations"
    print "-------------------------"
    for name, var in ncdataset.variables.items():
        if name in gmvarnames: continue   # skip over GM variables
        if hasattr(var, 'grid_mapping'):
            gmname = gmvardict.get(var.grid_mapping, '<undefined>')
            print "variable {0} => {1}".format(name, gmname)
    print

    # Close the netcdf file.
    ncdataset.close()


def rename(ncfile, options):
    """Rename a grid mapping variable and update all references to it."""

    if not options.gmname:
        print >>sys.stderr, "No grid mapping name specified via the --gmname option."
        return
    if not options.gmvname:
        print >>sys.stderr, "A new grid mapping variable name must be specified via the --gmvname option."
        return

    gmname = options.gmname
    newname = options.gmvname

    # Open a handle on the netcdf file.
    ncdataset = nc4.Dataset(ncfile, 'a')

    # Check that the requested grid mapping is present in the input file.
    oldname, var = get_grid_mapping_var(ncdataset, gmname)
    if not oldname:
        print >>sys.stderr, "No grid mapping called {0} was found in the input file.".format(gmname)
        ncdataset.close()
        return

    # Rename the grid mapping variable.
    ncdataset.renameVariable(oldname, newname)
    print "Renamed grid mapping variable from {0} to {1}".format(oldname, newname)

    # Update the grid_mapping attribute for any variables that reference the old GM variable.
    for name, var in ncdataset.variables.items():
        if getattr(var, 'grid_mapping', '') == oldname:
            var.grid_mapping = newname
            print "Relinked grid mapping for data variable {0}".format(name)

    # Close the netcdf file.
    ncdataset.close()


def unlink(ncfile, options):
    """Unlink the current grid mapping, if any, associated with one or more data variables."""

    # Check that one or more target variables (for unlinking) were specified.
    if not options.vars:
        print >>sys.stderr, "No target data variable(s) specified via the -v/--vars option."
        return

    # Open a handle on the netcdf file.
    ncdataset = nc4.Dataset(ncfile, 'a')

    for varname in options.vars.split(','):
        try:
            var = ncdataset.variables[varname]
            gmvname = getattr(var, 'grid_mapping', '')
            if gmvname:
                del var.grid_mapping
                print "Unlinked grid mapping {0} from data variable {1}".format(gmvname, varname)
        except:
            print "Requested variable called {0} not found - skipping".format(varname)
            continue

    # Close the netcdf file.
    ncdataset.close()


def find_grid_mapping_vars(ncdataset):
    """
    Find all netcdf variables which look like grid mapping variables, i.e. those that contain a
    'grid_mapping_name' attribute. Return a list of 2-tuples comprising the name of the variable
    and the variable object itself.
    """
    gmvars = []
    for name, var in ncdataset.variables.items():
        if 'grid_mapping_name' in var.ncattrs(): gmvars.append((name, var))
    return gmvars


def get_grid_mapping_var(ncdataset, gmname):
    """
    Return the netcdf variable with the specified grid mapping name, or ('', None) if it is not
    present.
    """
    for name, var in ncdataset.variables.items():
        if getattr(var, 'grid_mapping_name', '') == gmname: return (name, var)
    return ('', None)


def is_valid_gmname(gmname):
    """Test to see if gmname is a valid CF grid mapping name."""
    return gmname in CF_GRID_MAPPING_NAMES


def read_prop_file(filename, sep=None):
    """Read grid mapping properties from a text file and return them as a dictionary."""
    import string
    props = {}
    for line in open(filename, 'r').readlines():
        if not line: continue   # skip empty lines
        k,v = map(string.strip, line.strip().split(sep))
        for func in [int, float]:
            try:
                v = func(v)
                break
            except:
                pass
        props[k] = v
    return props


if __name__ == '__main__':
    main()
