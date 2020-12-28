#!/bin/sh
# Display the value of one or more netCDF attributes.
#
# Attribute names should be specified as :attname for global attributes
# or var:attname for variable attributes.
#
# Attributes (like 'history') which contain newline characters will be truncated
# since grep and sed, as used here, work on individual lines by default.

if [ $# -lt 2 ]; then
  echo "usage: ncattls ncfile attname [attname]..."
  echo "       attname = :attname or var:attname"
  exit 1
fi

ipfile=$1
shift
while [ $# -gt 0 ]
do
   if [[ ! $1 =~ .*:.+ ]]; then
      attname=:$1
   else
      attname=$1
   fi
   ncdump -hs ${ipfile} | grep "^\s*${attname}" | sed 's/^[ \t]*//' | sed 's/ *\;$//'
   shift
done
