# Copyright (c) 2013, Philip A.D. Bentley
# All rights reserved.
"""
sdttrans module - scientific data type translator

Includes functions for translating between various scientific data types, principally those used
within the met/ocean software community (numpy, netcdf, nco, etc).

As the source of the richest set of data types, NumPy acts as the central point for all the
supported translations. By which is meant that a type translation from grammar X to grammar Y
is effected as a translation from X to Numpy, then Numpy to Y, thus:

type X => type N => type Y

Author: Phil Bentley
Date: Jan 2013

As an aide-memoire the names and letter codes of the various NumPy scalar types are given below.

NumPy Type              Kind  Code  Remarks
----------              ----  ----  -------
bool_                   'b'   '?'   compat with python bool
bool8

byte (=int8)            'i'   'b'
short (=int16)          'i'   'h'
intc                    'i'   'i'
int_  (=int32)          'i'   'l'   compat with python int
intp                    'i'   'p'
longlong (int64)        'i'   'q'

ubyte (=uint8)          'u'   'B'
ushort (=uint16)        'u'   'H'
uintc                   'u'   'I'
uint (=uint32)          'u'   'L'   compat with python int
uintp                   'u'   'P'
ulonglong (=uint64)     'u'   'Q'

half (=float16)         'f'   'e'
single                  'f'   'f'   compat with C float
double                  'f'         compat with C double
float_ (=float32)       'f'   'd'   compat with python float
longfloat (=float64)    'f'   'g'

str_                    'S'   'S#'  where # = number of elements
unicode_                'U'   'U#'  where # = number of elements
object                        'O'

Note: complex types (kind='c') and void types (kind='V') are omitted from the above table since
they are not currently handled by this module.
"""
import sys
import numpy as np

# Figure out the size of Python int and float types on this platform
if sys.maxint > 2147483647 :
   platform_int  = 'int64'
   platform_uint = 'uint64'
else :
   platform_int  = 'int32'
   platform_uint = 'uint32'

if sys.float_info.mant_dig > 24 :
   platform_float  = 'float64'
else :
   platform_float  = 'float32'

# Symbolic constants for supported type grammars/ontologies.
(
CDL3_NS,
CDL4_NS,
NCML_NS,
NCO_NS,
NETCDF3_NS,
NETCDF4_NS,
NUMPY_NS
) = range(7)

# Map all non-numpy type names to numpy type names (np.dtype.name)
type_maps = {
   CDL3_NS: {'label': 'CDL3',
      'byte': 'int8', 'short': 'int16', 'int': 'int32', 'long': 'int32',
      'float': 'float32', 'real': 'float32', 'double': 'float64',
      'char': '|S1',
   },
   CDL4_NS: {'label': 'CDL4',
      'byte': 'int8', 'short': 'int16', 'int': 'int32', 'long': 'int32', 'int64': 'int64',
      'ubyte': 'uint8', 'ushort': 'uint16', 'uint': 'uint32', 'uint64': 'uint64',
      'float': 'float32', 'real': 'float32', 'double': 'float64',
      'char': '|S1', 'string': 'string_',
   },
   NCML_NS: {'label': 'NCML',
      'byte': 'int8', 'short': 'int16', 'int': 'int32', 'long': 'int32',
      'float': 'float32', 'double': 'float64',
      'char': '|S1', 'string': 'string_', 'String': 'string_',
   },
   NCO_NS: {'label': 'NCO',
      'b': 'int8', 's': 'int16', 'i': 'int32', 'l': 'int32', 'll': 'int64', 'int64': 'int64',
      'ub': 'uint8', 'us': 'uint16', 'u': 'uint32', 'ui': 'uint32', 'ul': 'int32',
      'ull': 'uint64', 'uint64': 'uint64',
      'f': 'float32', 'd': 'float64',
      'c': '|S1', 'sng': 'string_',
   },
   NETCDF3_NS: {'label': 'NETCDF CLASSIC',
      'NC_BYTE': 'int8', 'NC_SHORT': 'int16', 'NC_INT': 'int32', 'NC_LONG': 'int32',
      'NC_FLOAT': 'float32', 'NC_DOUBLE': 'float64', 'NC_CHAR': '|S1',
   },
   NETCDF4_NS: {'label': 'NETCDF-4',
      'NC_BYTE': 'int8', 'NC_SHORT': 'int16', 'NC_INT': 'int32', 'NC_LONG': 'int32', 'NC_INT64': 'int64',
      'NC_UBYTE': 'uint8', 'NC_USHORT': 'uint16', 'NC_UINT': 'uint32', 'NC_UINT64': 'uint64',
      'NC_FLOAT': 'float32', 'NC_DOUBLE': 'float64', 'NC_CHAR': '|S1', 'NC_STRING': 'string_',
   },
   NUMPY_NS: {'label': 'NumPy',
      'byte': 'int8', 'int8': 'int8',
      'short': 'int16', 'int16': 'int16',
      'int_': platform_int, 'int32': 'int32',
      'longlong': 'int64', 'int64': 'int64',
      'ubyte': 'uint8', 'uint8': 'uint8',
      'ushort': 'uint16', 'uint16': 'uint16',
      'uint': platform_uint, 'uint32': 'uint32',
      'ulonglong': 'uint64', 'uint64': 'uint64',
      'half': 'float16', 'float16': 'float16',
      'single': 'float32', 'double': 'float64',
      'float_': platform_float, 'float32': 'float32',
      'float64': 'float64',
      'str_': 'string_', 'string_': 'string_',
      'unicode_': 'unicode_',
      'bool_': 'bool_', 'bool8': 'bool_'
   },
}

# List of supported namespaces.
NAMESPACES = type_maps.keys()

#---------------------------------------------------------------------------------------------------
def translate(source_type, source_ns, target_ns=NUMPY_NS) :
#---------------------------------------------------------------------------------------------------
   """
   Translate source type from the source namespace to the target namespace.
   
   >>> translate('byte', CDL3_NS)
   'int8'
   >>> translate('byte', CDL3_NS, NCML_NS)
   'byte'
   >>> translate('ubyte', CDL4_NS, NCO_NS)
   'ub'
   >>> translate('short', NCML_NS)
   'int16'
   >>> translate('long', NCML_NS, NUMPY_NS)
   'int32'
   >>> translate('float', NCML_NS, NETCDF4_NS)
   'NC_FLOAT'
   >>> translate('ll', NCO_NS)
   'int64'
   >>> translate('int64', NUMPY_NS, NCO_NS)
   'll'
   >>> translate('ubyte', CDL3_NS, NCO_NS)
   Traceback (most recent call last):
       ...
   TypeError: Type 'ubyte' is not recognised in source namespace CDL3
   >>> translate('ui', NCO_NS, NETCDF3_NS)
   Traceback (most recent call last):
       ...
   TypeError: Source type 'ui' has no equivalent in target namespace NETCDF CLASSIC
   """
   assert source_ns in NAMESPACES , "Invalid source namespace"
   assert target_ns in NAMESPACES , "Invalid target namespace"
   assert source_ns != target_ns , "Source and target namespace are the same"

   if source_type not in type_maps[source_ns] :
      errmsg = "Type '%s' is not recognised in source namespace %s" % \
         (source_type, type_maps[source_ns]['label'])
      raise TypeError(errmsg)
   np_type = type_maps[source_ns][source_type]

   target_type = None
   if target_ns == NUMPY_NS :
      target_type = np_type
   else :
      for k,v in type_maps[target_ns].items() :
         if v == np_type :
            target_type = k
            break

   if not target_type :
      errmsg = "Source type '%s' has no equivalent in target namespace %s" % \
         (source_type, type_maps[target_ns]['label'])
      raise TypeError(errmsg)

   return target_type

#---------------------------------------------------------------------------------------------------
def get_numpy_type(source_type, source_ns) :
#---------------------------------------------------------------------------------------------------
   """
   Return the numpy data type - numpy.int8, numpy.uint32, numpy.float64, etc - corresponding to the
   specified source type and namespace. The returned type object may be used to create instances
   of that data type, as the following example illustrates:

   np_type = get_numpy_type(source_type, source_ns)
   x = np_type(value)   # value can be a number of string literal

   >>> get_numpy_type('real', CDL3_NS)
   <type 'numpy.float32'>
   >>> get_numpy_type('ubyte', CDL4_NS)
   <type 'numpy.uint8'>
   >>> get_numpy_type('real', NCML_NS)
   Traceback (most recent call last):
       ...
   TypeError: Type 'real' is not recognised in source namespace NCML
   """
   assert source_ns in NAMESPACES , "Invalid source namespace"
   if source_type not in type_maps[source_ns] :
      errmsg = "Type '%s' is not recognised in source namespace %s" % \
         (source_type, type_maps[source_ns]['label'])
      raise TypeError(errmsg)
   np_type = type_maps[source_ns][source_type]
   return np.dtype(np_type).type

#---------------------------------------------------------------------------------------------------
if __name__ == "__main__" :
#---------------------------------------------------------------------------------------------------
   """Run the doctests"""
   import doctest
   doctest.testmod()
