# BSDF Python lite implementation

This is a lightweight implementation of BSDF in Python. Fully functional
(including support for custom extensions) but no fancy features like lazy
loading or streaming. With less than 500 lines of code (including docstrings)
this demonstrates how simple a BSDF implementation can be.
See also the [complete version](python) of BSDF in Python.

## Installation

Copy [bsdf_lite.py](bsdf_lite.py) to a place where Python can find it.
There are no dependencies except Python 3.4+.


## Development

Run `invoke -l` in this directory for available tasks (like tests).


## Usage

```python
import bsdf_lite

# Setup a serializer with extensions and options
serializer = bsdf_lite.BsdfLiteSerializer(compression='bz2')

# Use it
bb = serializer.encode(my_object1)
my_object2 = serializer.decode(bb)
```


## Reference

### class `BsdfLiteSerializer(extensions=None, **options)`

Instances of this class represent a BSDF encoder/decoder.

This is a lite variant of the Python BSDF serializer. It does not support
lazy loading or streaming, but is otherwise fully functional, including
support for custom extensions.

It acts as a placeholder for a set of extensions and encoding/decoding
options. Options for encoding:

* compression (int or str): ``0`` or "no" for no compression (default),
  ``1`` or "zlib" for Zlib compression (same as zip files and PNG), and
  ``2`` or "bz2" for Bz2 compression (more compact but slower writing).
  Note that some BSDF implementations (e.g. JavaScript) may not support
  compression.
* use_checksum (bool): whether to include a checksum with binary blobs.
* float64 (bool): Whether to write floats as 64 bit (default) or 32 bit.


#### method `add_extension(extension_class)`

Add an extension to this serializer instance, which must be
a subclass of Extension.


#### method `remove_extension(name)`

Remove a converted by its unique name.


#### method `encode(ob)`

Save the given object to bytes.


#### method `save(f, ob)`

Write the given object to the given file object.


#### method `decode(bb)`

Load the data structure that is BSDF-encoded in the given bytes.


#### method `load(f)`

Load a BSDF-encoded object from the given file object.


##
### class `Extension()`

Base extension class to implement BSDF extensions for special data types.

Extension classes are provided to the BSDF serializer, which
instantiates the class. That way, the extension can be somewhat dynamic:
e.g. the NDArrayExtension exposes the ndarray class only when numpy
is imported.

A extension instance must have two attributes. These can be attribiutes of
the class, or of the instance set in ``__init__()``:

* name (str): the name by which encoded values will be identified.
* cls (type): the type (or list of types) to match values with.
  This is optional, but it makes the encoder select extensions faster. 

Further, it needs 3 methods:

* `match(value) -> bool`: return whether the extension can convert the
  given value. The default is ``isinstance(value, self.cls)``.
* `encode(value) -> encoded_value`: the function to encode a value to
  more basic data types.
* `decode(encoded_value) -> value`: the function to decode an encoded value
  back to its intended representation.


##

