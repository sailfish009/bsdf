# BSDF extensions

BSDF can be extended by providing the serializer with objects that can encode
certain data types using more basic data types.

This section specifies how certain objects can be encoded, and how these
extensions should be named. If everyone adheres to these specifcations, data
will be easier to share.

Data to be converted is identified by its identifier byte being in uppercase.
In such a case, there will be a string before the data, which identifies
the extension. Any data element can potentially be converted, even null.

How users specify extensions is specific to the implementation, but
extensions will generally consist of 4 elements:

* A name to identify it with. This will be encoded along with the data,
  so better keep it short. Custom extensions are best prefixed with
  the context (e.g. 'mylibrary.myextension'), to avoid name clashes.
* A type and/or a match function, so that the BSDF encoder can determine
  what objects must be serialized.
* An encoder function to convert the special object to more basic objects
  (can be of BSDF base types or types handled by lower level extensions).
* A decoder function to convert basic objects into the special data type.

BSDF defines standard extensions, which users are stongly encouraged
to follow, and which implementations are encouraged to support by
default. For custom extensions to work, a user should take care that the
extension is used during encoding and decoding. When an extension is not
available during decoding, the object is represented in its underlying
basic form.

This is a work in progress and the specifications below are subject to change.
The standardization of a base set of extensions should settle soonish after the
BSDF format itself has stabilized. 

It is worth noting that if an implementation does not support an extension and/or
the user did not specify a certain extension, the data will be loaded in its
"raw" form (e.g. a complex number as a list of two floats) and a warning will
be displayed.


### Complex numbers (standard)

* name: "c"
* encoding: a list with two elements (the real and the imaginary part).


### N-dimensional arrays (standard)

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


### 2D image data

* name: 'image2d'
* encoding: a 2D or 3D ndarray

If the data is 3D, it has shape[-1] channels.


### 3D image data

* name: 'image3d'
* encoding: a 3D or 4D ndarray

If the data is 4D, it has shape[-1] channels.
