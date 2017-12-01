# Binary Structured Data Format

The [Binary Structured Data Format](http://bsdf.readthedocs.io) (BSDF)
is an open specification for serializing (scientific) data, for the
purpose of storage and (inter process) communication.

It's designed to be a simple format, making it easy to implement in
many programming languages. However, the format allows implementations
to support powerful mechanics such as lazy loading of binary data, and
streamed reading/writing.

BSDF is a binary format; by giving up on human readability, BSDF can be simple,
compact and fast. See the [full specification](SPEC.md), or
how it [compares](COMPARISON.md) to other formats.


## Data types and extensions

BSDF supports 8 base types: null, booleans, integers, floats, strings/text,
(heterogenous) lists, mappings (i.e. dictionaries), and binary blobs. Integers
and floats represent 64 bit numbers, but can be encoded using less
bytes. Binary blobs can optionally be compressed (zlib or bz2), can have
checksums, and can be resized.

Via an efficient extension mechanism, other data types (including custom
ones), can be serialized. The standard [extensions](EXTENSIONS.md) work out
of the box, supporting e.g. nd-arrays and complex numbers.

## Status

Things are taking shape quickly, but at this point I still take the right to change
the spec without notice. Once I've collected some initial feedback, the spec
will be stable (before 2018). There are a few tasks left (#7) before I consider
it "mature".


## Implementations

Implementations currently exist for multiple languages. Each implementation is
[continuously tested](https://gitlab.com/almarklein/bsdf/pipelines) to ensure compatibility.

* The [Python](python) implementation in the form of [bsdf.py](python/bsdf.py).
* The [lite Python](python_lite) implementation in the form of [bsdf_lite.py](python_lite/bsdf_lite.py).
* The [Matlab / Octave](matlab) implementation in the form of [bsdf.m](matlab/bsdf.m).
* The [JavaScript](javascript) implementation in the form of [bsdf.js](javascript/bsdf.js).

We'd like implementations for other languages (such as R and Julia).
BSDF is designed to be easy to implement; perhaps you want to
[contribute](CONTRIBUTING.md)?


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

In JavaScript:

```js
> bsdf = require('bsdf.js')
{ encode: [Function: bsdf_encode],
  decode: [Function: bsdf_decode] }
> b = bsdf.encode(['just some objects', {foo: true, bar: null}, 42.001])
ArrayBuffer { byteLength: 48 }
> bsdf.decode(b)
[ 'just some objects', { foo: true, bar: null }, 42.001 ]
```

In Matlab / Octave:

```matlab
>> b = bsdf({'just some objects', struct('foo', true, 'bar', []), 42.001});
>> size(b)
ans =
   48    1
>> bsdf(b)
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
