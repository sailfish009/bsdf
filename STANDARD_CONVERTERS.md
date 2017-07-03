# Standard converters

This document specifies a standardised set of converters; a specifification
of how certain objects can be encoded, and how they are named.

This is a work in proggress and the specifications below are subject to change.
The standardization of a base set of convertes should settle soonish after the
BSDF format itself has stabalized. BSDF by itself is still useful, as one can
easily define one's own converters. Standardizing the converters is important
to easily share data though.


### Complex numbers 

* name: "c"
* encoding: a list with two elements (the real and the imaginary part).


### N-dimensional arrays

Questions:
    
* Allow F-order
* Allow stringing?
* Probably KISS, e.g. JS has no stringing.

* name: "ndarray"
* encoding: a dict with elements:
    * 'dtype', a string that specifies the data type. Minimal support
      should be 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32', 'uint64',
       'int64', 'float32', 'float64'.
    * 'shape', a list with as many elements (integers) as the array has dimensions.
    * 'data', a blob of bytes representing the contiguous data in C-order.


### 2D image data

* name: 'image2d'
* encoding: a 2D or 3D ndarray

If the data is 3D, it has shape[-1] channels.


### 3D image data

* name: 'image3d'
* encoding: a 3D or 4D ndarray

If the data is 4D, it has shape[-1] channels.

