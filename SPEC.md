# The BSDF format specification

This document applies to BSDF format
VERSION = 2.2.

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
* reading (closed and unclosed) streams (at the end of a data structure).
* preferably most standard extensions.

Implementations are encouraged to support:

* user-defined extensions.
* compressed binary blobs (zlib and bz2).

Further, implementations can be made more powerful by supporting:

* Lazy loading of blobs.
* Editing of (uncompressed) blobs.
* Lazy loading of streams.
* Deferred writing of streams.


## The format

Each data value is identified using a 1 byte character in the ASCII
range. If this identifier is a capital letter (smaller than ASCII 95),
it means that it's a value to be converted via an extension. If so, the next
item is a string (see below for its encoding) representing the extension name.
Next is the data itself. All words are stored in little endian format.


### Encoding of size

Sizes (of e.g. lists, mappings, strings, and blobs) are encoded as
follows: if the size is smaller than 251, a single byte (uint8) is used.
Otherwise, the first byte is 253, and the next 8 bytes represent the
size using an unsigned 64bit integer. (The bytes 254 and 255 are used to
identify (closed and unclosed) streams, and 251-252 are reserved.)

### Header

Data encoded with BSDF starts with the following 6-byte header:

* 4 Identifier bytes: ASCII `BSDF`, equivalent to 1178882882 little endian.
* Two variable size unsigned integers (uint8 in practice, assuming version
  numbers smaller than 251) indicating the major and minor version numbers.

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
* checksum: a single byte `0x00` means no hash, a byte `0xFF` means that
  there is, and is followed by a 16-byte md5 hash of the used (compressed) bytes.
* Byte alignment indicator: a uint8 number indicating the number of bytes
  to skip before the data starts. Implementations must align the data to 8-byte
  boundaries, but larger boundaries (up to 256) are allowed.
* Empty space: a number of empty bytes, as indicated by the byte alignment indicator.
* The binary blob, used_size bytes.
* Empty space, allocated_size minus used_size bytes. This space may have been
  caused by a reducion of size of the blob, or may be allocated to allow
  increasing the size of the blob.

Note: at this moment, some implementations can write checksums, but none
actually use it to validate the data. A policy w.r.t. checksums will have
to be made and implementations will have to implement this.

### lists

List values consist of the identifier `l` (for list), followed by a size item that
represents the length of the list n. After that, n values follow, which
can be of any type.

### mappings

Mappings, a.k.a. dictionaries or structs, consists of the identifier
`m` (for mapping), followed by a size item that represents the length
of the mapping n. After that, n items follow, each time a combination
of a string (the key) and the value.


## Streaming

Streams allow data to be written and read in a "lazy" fashion.
Implementations are not required to support streaming itself, but must
be able to read data that contains (closed and unclosed) streams.

Data that is "streaming" must always be the last object in the file
(except for its sub items). BSDF currently specifies that streaming is
only supported for lists. It will likely also be supported for blobs.

Streams are identified by the size encoding which starts with 254 or 255,
followed by an unsigned 64 bit integer. For closed streams (254), the integer
represents the number of items in the stream. For unclosed streams (255) the
64 bit integer must be ignored.

Encoder implementations can thus close a stream by changing the 255 to 254
and writing the real size in the next 8 bytes. Alternatively, an implementaion
can turn it into a regular encoded list (not streamed) by writing 253 instead.
Note that in the latter case the list can not be read as a stream anymore.
