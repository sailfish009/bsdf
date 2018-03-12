# Extending BSDF

BSDF can encode special kinds of data by providing the serializer with
extensions. How users specify extensions is specific to the
implementation, but they will typically consist of 4 elements:

* A name to identify it with. This will be encoded along with the data,
  so better keep it short, although custom extensions are best prefixed with
  the context (e.g. 'mylibrary.myextension'), to avoid name clashes.
* A type and/or a match function, so that the BSDF encoder can determine
  what objects must be serialized.
* An encoder function to convert the special object to more basic objects.
* A decoder function to reconstruct the special object from the basic objects.

### How it works

Extensions encode a high level data types into more basic data types, such
as the base BSDF types, or types supported by other extensions. Upon decoding,
the extension reconstructs the high level data from the "lower level" data.
When an extension is not available during decoding, a warning is produced, 
and the object is represented in its underlying basic form.

Extensions add very little overhead in speed (unlike e.g. JSON). In terms
of memory, each object being converted needs a little extra memory to encode
the extension's name.

### Kinds of extensions

Everyone can write their own extension and use it in their own work.

The purpose of this document is to specify ways to convert common data types,
and how these extensions should be named. If everyone adheres to these
specifcations, data will be easier to share.

BSDF also defines a small set of standard extensions, which users are stongly
encouraged to follow, and which all BSDF implementations are encouraged
to support by default.


### Status

This is a work in progress and the specifications below are subject to change.
The standardization of a base set of extensions should settle soonish after the
BSDF format itself has stabilized. 


## Standard extensions

### Complex numbers

* name: "c"
* encoding: a list with two elements (the real and the imaginary part).


### N-dimensional arrays

* name: "ndarray"
* encoding: a dict with elements:
    * 'dtype', a string that specifies the data type. Minimal support
      should be 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32',
      'float32', and preferably 'uint64', 'int64' and 'float64'.
    * 'shape', a list with as many elements (integers) as the array has
      dimensions. The first changing dimension first.
    * 'data', a blob of bytes representing the contiguous data.

We might add an "order" field at a later point. This will need to be
investigated/discussed further. Until then, C-order (row-major) should
be assumed where it matters.


## Other extensions

### 2D image data

* name: 'image2d'
* encoding: a dict with elements:
    * array: an ndarray with 2 or 3 dimensions
    * meta: a dict with arbitrary data

If the data is 3D, the 3d dimension represents the color channels
(1: L, 2: LA , 3: RGB or 4: RGBA).


### 3D image data

* name: 'image3d'
* encoding: a dict with elements:
    * array: an ndarray with 3 or 4 dimensions
    * meta: a dict with arbitrary data

If the data is 4D, the 3d dimension represents the color channels
(1: L, 2: LA , 3: RGB or 4: RGBA).
