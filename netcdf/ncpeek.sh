#!/bin/bash
#
# ncpeek: display information about the dimensions, variables or attributes
# in a netCDF file.
#
# Without any arguments, ncpeek functions exactly like the command
# $ ncdump -h file
#
# Attribute names can be specified as 'attname' or ':attname' for global attributes,
# or 'var:attname' for variable attributes (w/o the quotes in all cases)
#
# Attributes (such as 'history') which contain newline characters will be truncated
# since grep and sed, as used here, work on individual lines by default.

print_usage () {
   echo "usage: ncpeek [options] ncfile"
   echo
   echo "ncfile = the netCDF file to read"
   echo
   echo "OPTIONS"
   echo "   -a attname[,attname,...] - display named attributes"
   echo "   -d                       - display all dimensions"
   echo "   -g                       - display all global attributes"
   echo "   -v varname[,varname,...] - display named variables"
   echo "   -V                       - display all variable declarations w/o attributes"
   echo
   echo "Options may be combined as required. Without any options, ncpeek functions"
   echo "exactly like the command $ ncdump -h <file>"
   echo
   echo "For the -a option, attname can be specified as attname or :attname for a"
   echo "global-scope attribute, or as var:attname for a variable-scope attribute"
}

if [ $# -eq 0 ]; then
   print_usage
   exit 0
fi

# list of supported options
options=":a:dgv:V?"

# default settings
opt_set=0
dims_on=0
globals_on=0
vars_on=0
attlist=
varlist=

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
      a) attlist=$OPTARG ;
         opt_set=1 ;;
      d) dims_on=1 ;
         opt_set=1 ;;
      g) globals_on=1 ;
         opt_set=1 ;;
      v) varlist=$OPTARG ;
         opt_set=1 ;;
      V) vars_on=1 ;
         opt_set=1 ;;
      *) echo "unknown option: $OPTARG" ;
         exit 1 ;;
   esac
done

# get the netcdf file argument
shift $(($#-1))
ncfile=$1

# if no options have been specified just do the equivalent of ncdump -h
if [[ $opt_set -eq 0 ]]; then
   ncdump -h ${ncfile}
   exit 0
fi

# display global attributes
if [ $globals_on -eq 1 ]; then
   echo "// global attributes:"
   ncdump -hs ${ncfile} | egrep "^\s+:.*"  | sed 's/ *\;$//'
fi

# display dimension info
if [ $dims_on -eq 1 ]; then
   echo "dimensions:"
   ncdump -hs ${ncfile} | egrep "^\s+(\w|_)+\s*=.*" | sed 's/ *\;$//'
fi

# display variable info
if [ $vars_on -eq 1 ]; then
   echo "variables:"
   ncdump -hs ${ncfile} | egrep "^\s+\w+\s+(\w|_)+\(.*\).*" | sed 's/ *\;$//'
fi

# display requested attributes
if [ -n "$attlist" ]; then
   for att in ${attlist//,/ }
   do
      if [[ ! $att =~ .*:.+ ]]; then
         attname=:$att
      else
         attname=$att
      fi
      ncdump -hs ${ncfile} | egrep "^\s+${attname}" | sed 's/ *\;$//'
   done
fi

# display requested variables
if [ -n "$varlist" ]; then
   for var in ${varlist//,/ }
   do
      ncdump -hs ${ncfile} | egrep "^\s+\w+\s+${var}+\(.*\).*" | sed 's/ *\;$//'
      ncdump -hs ${ncfile} | egrep "^\s+${var}:.*" | sed 's/ *\;$//'
   done
fi

exit 0
