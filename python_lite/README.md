# BSDF Python lite implementation

This is a lightweight implementation of BSDF in Python. Fully functional
(including support for custom converters) but no fancy features like lazy
loading or streaming. With less than 500 lines of code (including docstrings)
this demonstrates how simple a BSDF implementation can be.
See also the [complete version](python) of BSDF in Python.

## Installation

Copy [bsdf_lite.py](bsdf_lite.py) to a place where Python can find it.
There are no dependencies except Python 3.4+.


## Development

Run `invoke -l` in this directory for available tasks (like tests).


## Usage

<pre style='font-size:80%;'>
import bsdf_lite

# Setup a serializer with converters and options
serializer = bsdf_lite.BsdfLiteSerializer([bsdf_lite.complex_converter],
                                          compression='bz2')
# Use it
bb = serializer.saveb(my_object1)
my_object2 = serializer.loadb(bb)
</pre>


## Reference

### class BsdfLiteSerializer`(converters=None, **options)`

Instances of this class represent a BSDF encoder/decoder.

This is a lite variant of the Python BSDF serializer. It does not support
lazy loading or streaming, but is otherwise fully functional, including
support for custom converters.

It acts as a placeholder for a set of converters and encoding/decoding
options. Options for encoding:

* compression (int or str): ``0`` or "no" for no compression (default),
  ``1`` or "zlib" for Zlib compression (same as zip files and PNG), and
  ``2`` or "bz2" for Bz2 compression (more compact but slower writing).
* use_checksum (bool): whether to include a checksum with binary blobs.
* float64 (bool): Whether to write floats as 64 bit (default) or 32 bit.


#### method add_converter`(name, cls, encoder, decoder)`

Add a converter to this serializer instance, consisting of:

* name (str): a unique name for this converter (less than 251 chars).
* cls (type): the class to use in ``isinstance`` during encoding, or
  a list of classes to trigger on.
* encoder (function): the function to encode an instance with,
  which should return a structure of encodable objects.
* decoder (function): the function to decode the aforementioned
  structure with.


#### method remove_converter`(name)`

Remove a converted by its unique name.


#### method saveb`(ob)`

Save the given object to bytes.


#### method save`(f, ob)`

Write the given object to the given file stream.


#### method loadb`(bb)`

Load the data structure that is BSDF-encoded in the given bytes.


#### method load`(f)`

Load a BSDF-encoded object from the given stream.


##

