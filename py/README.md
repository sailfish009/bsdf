# BSDF Python implementation

This is the reference implementation of BSDF, with support for streamed
reading and writing, and lazy loading of binary blobs.

This directory also contains tooling to help test other BSDF
implementations, most notably bsdf_test_service.py.


## Installation

At this point, copy [bsdf.py](bsdf.py) to a place where Python can find it.
There are no dependencies except Python 2.7 or Python 3.4+.


## Development

Run `invoke -l` in this directory for available tasks (like tests).


## Usage

<pre style='font-size:80%;'>
import bsdf

# Simple use ...

# Encode
bb = bsdf.saveb(my_object)
# Decode
my_object2 = bsdf.loadb(bb)

# Advanced use ...

# Setup a serializer with converters and options
serializer = bsdf.BsdfSerializer([bsdf.complex_converter],
                                 compression='bz2')
# Use it
bb = serializer.saveb(my_object1)
my_object2 = serializer.loadb(bb)
</pre>


## Reference

### class BsdfSerializer`(converters=None, **options)`

Instances of this class represent a BSDF encoder/decoder.

It acts as a placeholder for a set of converters and encoding/decoding
options. Use this to predefine converters and options for high
performance encoding/decoding. For general use, see the functions
`save()`, `saveb()`, `load()`, and `loadb()`.

This implementation of BSDF supports streaming lists (keep adding
to a list after writing the main file), lazy loading of blobs, and
in-place editing of blobs (for streams opened with a+).

Options for encoding:

* compression (int or str): ``0`` or "no" for no compression (default),
  ``1`` or "zlib" for Zlib compression (same as zip files and PNG), and
  ``2`` or "bz2" for Bz2 compression (more compact but slower writing).
* use_checksum (bool): whether to include a checksum with binary blobs.
* float64 (bool): Whether to write floats as 64 bit (default) or 32 bit.

Options for decoding:

* load_streaming (bool): if True, and the final object in the structure was
  a stream, will make it available as a stream in the decoded object.
* lazy_blob (bool): if True, bytes are represented as Blob objects that can
  be used to lazily access the data, and also overwrite the data if the
  file is open in a+ mode.


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
### function saveb`(ob, converters=None, **options)`

Save (BSDF-encode) the given object to bytes.
See `BSDFSerializer` for details on converters and options.


### function save`(f, ob, converters=None, **options)`

Save (BSDF-encode) the given object to the given filename or
file object. See` BSDFSerializer` for details on converters and options.


### function loadb`(bb, converters=None, **options)`

Load a (BSDF-encoded) structure from bytes.
See `BSDFSerializer` for details on converters and options.


### function load`(f, converters=None, **options)`

Load a (BSDF-encoded) structure from the given filename or file object.
See `BSDFSerializer` for details on converters and options.



