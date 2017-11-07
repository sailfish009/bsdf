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
my_object2 = bsdf.decode(bb)
```
Advanced use:

```python
import bsdf

class MyFunctionExtension(bsdf.Extension):
    """ An extension that can encode function objects and reload them if the
    function is in the global scope.
    """
    name = 'my.func'
    def match(self, f):
        return callable(f)
    def encode(self, f):
        return f.__name__
    def decode(self, name):
        return globals()[name]  # in reality, one would do a smarter lookup here

# Setup a serializer with extensions and options
serializer = bsdf.BsdfSerializer([MyFunctionExtension],
                                 compression='bz2')

def foo():
    print(42)

# Use it
bb = serializer.encode(foo)
foo2 = serializer.decode(bb)

foo2()  # print 42
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

