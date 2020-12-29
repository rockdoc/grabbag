"""
A selection of experimental functions and classes for iterating sequentially
over data chunks in a netcdf variable.

Motivation: the netcdf4-python module provides access to netcdf variables via the
netCDF4.Variable class. However, while instances of this class support fairly rich
access to the data payload via the familiar slicing syntax (e.g. var[0:m,0:n,...]),
there is at present no convenient mechanism for iterating sequentially over the
blocks of data that comprise a chunked netcdf-4 variable. Such a capability can be
desirable in those situations where large datasets are stored in netcdf-4 files
that make use of the chunking features of the underlying HDF5 storage scheme.

This module presents a handful of solutions - some function-based, some class-based -
to get round this limitation.

For an introduction to Python iterators and generators, check out the following
links (plenty more like these on the web):

- http://excess.org/article/2013/02/itergen1
- http://www.itmaybeahack.com/book/python-2.6/html/p02/p02c08_generators.html
"""

from itertools import product
import math
import netCDF4


# Define a utility class for representing a netcdf data chunk and its hyperslab
# coordinates.
class NcDataChunk(object):
    """
    Trivial class for representing a chunk of data from a netcdf variable.
    Instances provide a handle to the data (a numpy array), plus the index-space
    coordinates (aka hyperslab) of the data chunk within the original source data.
    """
    def __init__(self, data, coords):
        self.data = data
        self.coords = coords

    def __str__(self):
        return "data(shape={0.shape}, dtype={0.dtype}), space={1}".format(
            self.data, self.coords)


# Define a utility function for generating hyperslab definitions for a given
# array and chunk shape. This function gets called by each of the solutions
# described later. A hyperslab definition is a list of one or more fully-specified
# slice objects, e.g. [slice(0, 2, 1), slice(0, 4, 1), ...]. The step (=stride)
# component is always set to 1 in order that no data is skipped.
def iter_hyperslabs(array_shape, chunk_shape):
    """
    Generator function for iterating over the hyperslab objects that define
    successive data chunks of an n-D array of the given shape.
    """
    # This code could be compressed into a single list comprehension, albeit a
    # fairly obtuse one.
    hyperslabs = []
    for dim in range(len(array_shape)):
        stop = array_shape[dim]
        step = chunk_shape[dim]
        hyperslabs.append([slice(i,min(i+step,stop),1) for i in range(0,stop,step)])

    for hyperslab in product(*hyperslabs):
        yield hyperslab


# Solution 1
# ----------
# Define a generator function which yields successive data chunks for the
# specified netcdf variable, var. This is the simplest and safest solution.


def iter_chunks(var):
    """
    Iterate over the chunks in a netCDF variable in C order. If variable var
    is not chunked (i.e. it's contiguous) then a single chunk representing the
    entire variable is returned. Each iteration returns an NcDataChunk object,
    which provides access to the numpy array for the chunk as well as the index-
    space coordinates of the chunk within the netcdf variable. Note that the
    data chunk is a separate numpy array rather than a view into the source
    array owned by the var object. This means that changes to the chunk array
    do not get applied to the source array by default.
    """

    # Get the chunk shape, if any, used by the variable.
    chunkshape = var.chunking()

    # If variable is contiguous then set chunk shape equal to variable shape.
    if not isinstance(chunkshape, (list, tuple)):
        chunkshape = var.shape

    # Loop over all chunk-sized hyperslabs.
    for hyperslab in iter_hyperslabs(var.shape, chunkshape):
        yield NcDataChunk(var[hyperslab], hyperslab)


# Solution 2
# ----------
# Define a proxy class which contains a reference to the actual netcdf variable
# object. Actually, this may be an Adapter class rather than a Proxy class since
# it extends (adapts) the interface of the netCDF4.Variable class.


class ProxyNcVariable(object):
    """
    Put a wrapper around a netcdf variable so that it can be iterated over in
    data chunks whose size is defined by the variable's chunking settings. In
    the case of variables that use contiguous data storage (which includes ALL
    netcdf-3 variables), a single data chunk is returned.
    """

    def __init__(self, var):
        """Initialize an instance object."""
        self._var = var     # reference to the actual netcdf variable object
        self._nchunks = None

    def __getattr__(self, attr):
        """Hand off any other attribute/method requests to the real variable."""
        return getattr(self._var, attr)

    # Note that the __iter__ method is written as a generator function.
    # Therefore we don't need to define a next() method within this class.
    def __iter__(self):
        """Iterate over all data chunks"""
        for hs in iter_hyperslabs(self._var.shape, self._chunkshape):
            yield self._var[hs]

    @property
    def hyperslabs(self):
        """Return a list of hyperslab objects that define all data chunks."""
        return list(iter_hyperslabs(self._var.shape, self._chunkshape))

    @property
    def nchunks(self):
        """Return the total number of chunks comprising the variable."""
        if self._nchunks is None:
            self._nchunks = 1
            for i in range(len(self._var.shape)):
                self._nchunks *= int(math.ceil(float(self._var.shape[i])/self._chunkshape[i]))
        return self._nchunks

    @property
    def varname(self):
        """Return the name of the underlying netCDF variable."""
        return self._var._name

    @property
    def _chunkshape(self):
        """Return the shape of each data chunk as a tuple."""
        chunkshape = self._var.chunking()
        if not isinstance(chunkshape, (list, tuple)) : chunkshape = self._var.shape
        return chunkshape


# Solution 3
# ----------
# Define a subclass of netCDF4.Variable with added iteration capabilities.
# This solution may not work reliably because the Variable class typically is
# never instantiated directly by the user; rather the dataset.createVariable()
# method is normally used to create Variable instance objects.


class NcIterableVariable(netCDF4.Variable):
    """Adds chunk-based iteration capabilities to netCDF4.Variable objects."""

    # Instead of using __init__ to modify the state of an instance object we
    # use __new__ to create and return a new instance; for an explanation see
    # http://www.python.org/download/releases/2.2.3/descrintro/#__new__
    def __new__(cls, group, varname, datatype, **kwargs):
        """
        Return an instance of the crrent class. This method takes the same
        positional and keyword arguments as the netCDF4.Variable constructor.
        """
        var = netCDF4.Variable.__new__(cls, group, varname, datatype, **kwargs)
        group.variables[varname] = var
        return var

    # Note that the __iter__ method is written as a generator function.
    # Therefore we don't need to define a next() method within this class.
    def __iter__(self):
        """Iterate over all data chunks"""
        for hs in iter_hyperslabs(self.shape, self._chunkshape):
            yield self[hs]

    @property
    def hyperslabs(self):
        """Return a list of hyperslab objects that define all data chunks"""
        return list(iter_hyperslabs(self.shape, self._chunkshape))

    @property
    def nchunks(self):
        """Return the total number of chunks comprising the variable."""
        n = 1
        for i in range(len(self.shape)):
            n *= int(math.ceil(float(self.shape[i])/self._chunkshape[i]))
        return n

    @property
    def varname(self):
        """Return the name of this variable."""
        return self._name

    @property
    def _chunkshape(self):
        """Return the shape of each data chunk as a tuple."""
        chunkshape = self.chunking()
        if not isinstance(chunkshape, (list, tuple)) : chunkshape = self.shape
        return chunkshape


# Solution 4
# ----------
# Apply a new mix-in class to the NcVariable user-defined class. This solution
# is functionally equivalent to solution 3. The only difference is that the
# iteration functionality is encapsulated within a separate mix-in class which
# could, in theory, be applied to several suitable target classes. In practice
# the opportunity to exploit this technique in the current scenario is probably
# very limited (or non-existent), in which case the solution is less attractive
# than the other solutions presented here.


# This is the mix-in class. It adds iteration capabilities to a recipient class.
class NcChunkIteratorMixIn(object):
    """
    A mix-in class which provides methods for iterating over chunks of data
    stored in netCDF variables.
    """

    # Note that the __iter__ method is written as a generator function.
    # Therefore we don't need to define a next() method within this class.
    def __iter__(self):
        """Iterate over all data chunks"""
        for hs in iter_hyperslabs(self.shape, self._chunkshape):
            yield self[hs]

    @property
    def hyperslabs(self):
        """Return a list of hyperslab objects that define all data chunks"""
        return list(iter_hyperslabs(self.shape, self._chunkshape))

    @property
    def nchunks(self):
        """Return the total number of chunks comprising the variable."""
        n = 1
        for i in range(len(self.shape)):
            n *= int(math.ceil(float(self.shape[i])/self._chunkshape[i]))
        return n

    @property
    def _chunkshape(self):
        """Return the shape of each data chunk as a tuple."""
        chunkshape = self.chunking()
        if not isinstance(chunkshape, (list, tuple)) : chunkshape = self.shape
        return chunkshape


# This is the target class to which we will add iteration capabilities.
class NcVariable(netCDF4.Variable, NcChunkIteratorMixIn):
    """
    Extends the netCDF4.Variable class by defining additional local methods
    (just varname at present) and by inheriting iteration functionality from
    the NcChunkIteratorMixIn mix-in class.
    """

    # see notes under NcIterableVariable.__new__
    def __new__(cls, group, varname, datatype, **kwargs):
        """
        Return an instance of the NcVariable class. This method takes the same
        positional and keyword arguments as the netCDF4.Variable constructor.
        """
        var = netCDF4.Variable.__new__(cls, group, varname, datatype, **kwargs)
        group.variables[varname] = var
        return var

    @property
    def varname(self):
        """Return the name of this variable."""
        return self._name
