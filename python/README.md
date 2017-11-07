# BSDF Python implementation

This is the reference implementation of BSDF, with support for streamed
reading and writing, and lazy loading of binary blobs. See also the
[minimal version](python_lite) of BSDF in Python.


## Installation

At this point, copy [bsdf.py](bsdf.py) to a place where Python can find it.
There are no dependencies except Python 2.7 or Python 3.4+.


## Development

Run `invoke -l` in this directory for available tasks (like tests).


## Usage

Simple use:

```python
import bsdf

# Encode
bb = bsdf.encode(my_object)

# Decode
my_object2 = bsdf.loadb(bb)
```
Advanced use:

```python

# Setup a serializer with extensions and options
serializer = bsdf.BsdfSerializer([bsdf.ComplexExtension],
                                 compression='bz2')
# Use it
bb = serializer.encode(my_object1)
my_object2 = serializer.loadb(bb)
```


## Reference

### function `encode(ob, extensions=None, **options)`

Save (BSDF-encode) the given object to bytes.
See `BSDFSerializer` for details on extensions and options.


### function `decode(bb, extensions=None, **options)`

Load a (BSDF-encoded) structure from bytes.
See `BSDFSerializer` for details on extensions and options.


### function `save(f, ob, extensions=None, **options)`

Save (BSDF-encode) the given object to the given filename or
file object. See` BSDFSerializer` for details on extensions and options.


### function `load(f, extensions=None, **options)`

Load a (BSDF-encoded) structure from the given filename or file object.
See `BSDFSerializer` for details on extensions and options.


### class `BsdfSerializer(extensions=None, **options)`

Instances of this class represent a BSDF encoder/decoder.

It acts as a placeholder for a set of extensions and encoding/decoding
options. Use this to predefine extensions and options for high
performance encoding/decoding. For general use, see the functions
`save()`, `encode()`, `load()`, and `decode()`.

This implementation of BSDF supports streaming lists (keep adding
to a list after writing the main file), lazy loading of blobs, and
in-place editing of blobs (for streams opened with a+).

Options for encoding:

* compression (int or str): ``0`` or "no" for no compression (default),
  ``1`` or "zlib" for Zlib compression (same as zip files and PNG), and
  ``2`` or "bz2" for Bz2 compression (more compact but slower writing).
  Note that some BSDF implementations (e.g. JavaScript) may not support
  compression.
* use_checksum (bool): whether to include a checksum with binary blobs.
* float64 (bool): Whether to write floats as 64 bit (default) or 32 bit.

Options for decoding:

* load_streaming (bool): if True, and the final object in the structure was
  a stream, will make it available as a stream in the decoded object.
* lazy_blob (bool): if True, bytes are represented as Blob objects that can
  be used to lazily access the data, and also overwrite the data if the
  file is open in a+ mode.


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

