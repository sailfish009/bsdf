# Binary Structured Data Format

The [Binary Structured Data Format](http://bsdf.io) (BSDF)
is an open specification for serializing (scientific) data, for the
purpose of storage and (inter process) communication.

It's designed to be a simple format, making it easy to implement in
many programming languages. However, the format allows implementations
to support powerful mechanics such as lazy loading of binary data, and
streamed reading/writing.

BSDF is a binary format; by giving up on human readability, BSDF can be simple,
compact and fast. See the [full specification](SPEC.md), or
how it [compares](COMPARISON.md) to other formats.

The source code is at [Gitlab](http://gitlab.com/almarklein/bsdf).


## Data types and extensions

BSDF supports 8 base types: null, booleans, integers, floats, strings/text,
(heterogenous) lists, mappings (i.e. dictionaries), and binary blobs. Integers
and floats represent 64 bit numbers, but can be encoded using less
bytes. Binary blobs can optionally be compressed (zlib or bz2), can have
checksums, and can be resized.

Via an efficient [extension mechanism](EXTENSIONS.md), other data types (including custom
ones), can be serialized. The standard extensions work out
of the box, supporting e.g. nd-arrays and complex numbers.


## Status

The format is complete, except for a few details such us how to deal with
blob checksums. All implementations comply with the format and are well-tested.
We could do with implementatations in additional languages though!


## Implementations

Implementations currently exist for multiple languages. Each implementation is
[continuously tested](https://gitlab.com/almarklein/bsdf/pipelines) to ensure compatibility.

* The [Python](python) implementation in the form of [bsdf.py](python/bsdf.py).
* The [lite Python](python_lite) implementation in the form of [bsdf_lite.py](python_lite/bsdf_lite.py).
* The [Matlab / Octave](matlab) implementation in the form of [Bsdf.m](matlab/Bsdf.m).
* The [JavaScript](javascript) implementation in the form of [bsdf.js](javascript/bsdf.js).

We'd like implementations for other languages (such as R and Julia).
BSDF is designed to be easy to implement; perhaps you want to
[contribute](CONTRIBUTING.md)?

We aim for the implementations to have similar API's: a class whose
instances hold extensions and options, and has `encode()`, `decode()`,
`save()`,`load()`, and `add_extension()` methods. Optionally, an implementation
can provide convenience functions.

There is also a [command line interface](CLI.md) that can be used to e.g.
create and view BSDF files.

## Installation

See the specific implementations for detailed installation instructions.
Most implementations consist of a single file.


## Examples


In Python:

```py
>>> import bsdf
>>> b = bsdf.encode(['just some objects', {'foo': True, 'bar': None}, 42.001])
>>> b
b'BSDF\x02\x00l\x03s\x11just some objectsm\x02\x03fooy\x03barvd\xe3\xa5\x9b\xc4 \x00E@'
>>> len(b)
48
>>> bsdf.decode(b)
['just some objects', {'foo': True, 'bar': None}, 42.001]
```

See more Python examples, see the [Python example notebook](https://gitlab.com/almarklein/bsdf/blob/master/python/bsdf_example_python.ipynb).

In JavaScript:

```js
> bsdf = require('bsdf.js')
{ encode: [Function: bsdf_encode],
  decode: [Function: bsdf_decode],
  BsdfSerializer: [Function: BsdfSerializer],
  standard_extensions: ...}
> b = bsdf.encode(['just some objects', {foo: true, bar: null}, 42.001])
ArrayBuffer { byteLength: 48 }
> bsdf.decode(b)
[ 'just some objects', { foo: true, bar: null }, 42.001 ]
```

In Matlab / Octave:

```matlab
>> bsdf = Bsdf()
>> b = bsdf.encode({'just some objects', struct('foo', true, 'bar', []), 42.001});
>> size(b)
ans =
   48    1
>> bsdf.decode(b)
ans =
{
  [1,1] = just some objects
  [1,2] =

    scalar structure containing the fields:

      foo = 1
      bar = [](0x0)

  [1,3] =  42.001
}
```

It is worth noting that although different languages may represent data types
in slightly different ways, the underlying bytes in BSDF are the same. This makes
BSDF suited for inter-language communication.


## License

In principal, all implementations in the BSDF repository use the
2-clause BSD license (see LICENSE for details), unless otherwise
specified. All code is liberally licensed (BSD- or MIT-like).
