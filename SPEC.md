# BSDF format specification


## Purpose and features

The purpose of BSDF is to provide a data format that is ...

* easy to implement, such that it can easily spread to other programming languages.
* suitable for working with binary (scientific) data.
* suitable for inter process communication and the web.

This has resulted in the following features:

* A binary format that has a simple specification.
* Language agnostic and machine independent.
* Compact storage.
* Fast encoding and decoding. E.g. the pure Python implementation has
  a respectable speed, and can be made faster via e.g. a C implementation.
* Support for binary blobs, in uncompressed format or compression with zlib or bz2.
* Uses data types that are widely supported in most languages.
* Provides a mechanism to easily convert to/from special data types,
  with minimal effect on performance, also accross languages.
* Data can be read and written without seek operations (e.g. to allow
  (streamed) reading from remote resources).
* Zero copy reads (in uncompressed data, bytes are aligned).
* Implementations can provide direct access to blobs via a file-like
  object for lazy loading or efficient updating.
* Provides a way to stream data (e.g. as a list at the end of the
  file that can simply be appended to).

Also see how BSDF [compares](COMPARISON.md) to other formats.


## Minimal implementation

A minimal BSDF implementation must support:

* the basic data types: null, bool, int, float, string, list, mapping,
  and uncompressed binary blobs.
* reading unclosed streams (at the end of a data structure).
* preferably most standard converters.

Implementations are encouraged to support:

* user-defined converters.
* compressed binary blobs (zlib and bz2).

Further implementations can be made more powerful by supporting:

* Lazy loading of blobs.
* Lazy loading of streams.
* Deferred writing of streams.


## The format

Each data value is identified using a 1 byte character in the ASCII
range. If this identifier is a capital letter (smaller than ASCII 95),
it means that it's a value to be converted. If so, the next item is a
string (see below for its encoding) representing the converter name.
Next is the data itself. All words are stored in little endian format.


### Encoding of size

Sizes (of e.g. lists, mappings, strings, and blobs) are encoded as
follows: if the size is smaller than 251, a single byte (uint8) is used.
Otherwise, the first byte is 253, and the next 8 bytes represent the
size using an unsigned 64bit integer. (The byte 255 is used to identify
streams, and 251-254 are reserved.)

### Header

Data encoded with BSDF starts with the following 6-byte header:

* 4 Identifier bytes: ASCII `BSDF`, equivalent to 1178882882 little endian.
* Two variable size unsigned integers (uint8 in practice, assuming version
  number are smaller than 251) indicating major and minor version
  numbers. Currently 2 and 0.

### null

The value null/nil/none is identified by `v` (for void), and has no data.

### booleans

The values false and true are identified by `n` for no, and `y` for yes,
respectively. These values have no data.

### integers

Integer values come it two flavours:

* `h`: small values (between -32768 and 32768, inclusive) can be encoded using int16.
* `i`: int64

### floats

Floats values follow the IEEE 754 standard, can be `NaN` and `inf` and
come in two flavours:

* `f`: a 32bit float
* `d`: a 64bit float

### strings

String values are identified by `s` (for string), and consists of a
size item (1 or 9 bytes), followed by the bytes that represents the
UTF-8 encoded string.

### blobs

Binary data is encoded as follows:

* char `b` (for blob)
* uint8 value indicating the compression. 0 means no compression, 1 means zlib,
  2 means bz2.
* allocated_size: the amount of space allocated for the blob, in bytes.
* used_size: the amount of used space for the blob, in bytes.
* data_size: the size of the blob when decompressed, in bytes. If compression
  is off, it must be equal to used_size.
* Optonal checksum: a single byte `0x00` means no hash, a byte `0xFF` means that
  there is, and is followed by a 16-byte md5 hash of the used (compressed) bytes.
* Byte alignment indicator: a uint8 number (0-7) indicating the number of bytes
  to skip before the data starts. 
* Empty space: n empty bytes, as indicated by the byte alignment indicator.
* The binary blob, used_size bytes.
* Empty space, allocated_size minus used_size bytes.


### lists

List values consist of the identifier `l` (for list), followed by a size item that
represents the length of the list n. After that, n values follow, which
can be of any type.

### mappings

Mappings, a.k.a. dictionaries or structs, consists of the identifier
`m` (for mapping), followed by a size item that represents the length
of the mapping n. After that, n items follow, each time a combination
of a string that represents the key, and the value itself.


## Streaming

Streams allow data to be written and read in a "lazy" fashion.
Implementations are not required to support streaming itself, but must
be able to read data with (unclosed) streams.

Data that is "streaming" must always be the last object in the file
(except for its sub items). BSDF currently specifies that streaming is
only supported for lists. It will likely also be added for blobs.

Streams are identified by the size encoding which starts with 255,
followed by an unsigned 64 bit integer. This allows to later "close"
the stream by changing the 255 to 253 and writing the real size in the next 8
bytes.


## Converters

This section specifies a set of converters; a specifification
of how certain objects can be encoded, and how they are named.

Data to be converted is identified by its identifier byte to be in uppercase.
In such a case, there will be a string before the data, which identifies
the converter. Any data element can potentially be converted, even null.

How users specify converters is specific to the implementation, but
converters will generally consist of 4 elements:

* A name to identify it with. This will be encoded along with the data,
  so better keep it short. Custom converters do well to prefix the name with
  the context (e.g. 'mylibrary.myconverter'), to avoid name clashes.
* A type, so that the BSDF encoder can use the converter when an object
  of such type is being serialized.
* An encoder function to convert the special object to more basic
  objects (although these can again be convertable).
* A decoder function to convert basic objects into the special data type.

We distinguish between regular converters, which should be seen as a
suggestion by which certain types of data can be encoded, and standard
converters, which users are stongly encouraged to follow, and which
implementations are encouraged to support by default.

This is a work in progress and the specifications below are subject to change.
The standardization of a base set of convertes should settle soonish after the
BSDF format itself has stabalized. 

It is worth noting that if an implementation does not support a converter and/or
the user did not specify a certain converter, the data will be loaded in its
"raw" form (e.g. a complex number as a list of two floats) and a warning will
be displayed.


### Complex numbers (standard)

* name: "c"
* encoding: a list with two elements (the real and the imaginary part).


### N-dimensional arrays (should be standard soon)

Questions:
    
* Allow F-order?
* Allow striding?
* Probably KISS, e.g. JS has no striding.

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
