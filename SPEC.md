# BSDF format specification

## Purpose

The purpose of BSDF is to provide a data format that is easy to
implement, suitable for storing binary (scientific) data and fast enough
for use in inter-process communications.


## Features

The goals of BSDF are quite similar to the ASDF format, except that BSDF
traded human readability for a simpler format, faster encoding/decoding
and more compact storage (for the tree, not so much of the data blobs).

* A binary format that has a simple specification and is (relatively)
  easy to implement.
* Pretty compact storage, pretty fast encoding and decoding with naive
  (e.g. pure Python) implementation. Very fast encoding/decoding
  possible via e.g. C implementations.
* Support for binary blobs, in uncompressed format, or compression with zlib or bz2.
* Uses data types that are widely supported in most languages.
* Provides a mechanism to easily convert to/from special data types,
  with minimal effect on performance.
* Data can be read and written without seek operations.
* Provides direct access to blobs via file object for lazy loading or
  efficient updating.
* Provides a way to stream binary data (via a blob at the end of the
  file that can simply be appended to).


## The format

* 4 Identifier bytes: ASCII "BSDF", equivalent to an uint32 1112753222 big endian
  or 1178882882 little endian.
* Two variable size unsigned integers (uint8 in practice) indicating major and
  minor version numbers. Currently 2 and 0.
* the data

Each data value is identified using a 1 byte character. If this
identifier is a capital letter (smaller than ASCII 95), it means that
it's a value to be converted. If so, the next item is a string (see
below for its encoding) representing the converter name. Next is the
data itself.

### Encoding of size

The size of lists, mappings and blob sizes are encoded as follows: if
the size is smaller than 251, a single byte (uint8)
is used. Otherwise, the first byte is 253, and the next 8 bytes represent
the size using an unsigned 64bit integer (little endian).

### null, false, true

The values `null`, `false` and `true` are identified by 'v' (for void),
'n' for no, and 'y' for yes, respectively.

### integers

Integer values come it two flavours:
* 'u': small values (between 0 and 255) can be encoded using a uint8.
* 'i': int64

### floats

Floats values follow the IEEE 754 standard, can be `NaN` and `inf` and
come in two flavours:
* 'f': a 32bit float
* 'd': a 64bit float

### strings

String values are identified by 's', and consists of a size item (1 or
9 bytes), followed by the bytes that represents the UTF-8 encoded
string.

### blobs

Binary data is encoded as follows:

* char 'b' (for blob)
* uint8 value indicating the compression. 0 means no compression, 1 means zlib,
  2 means bz2.
* allocated_size: the amount of space allocated for the blob, in bytes.
* used_size: the amount of used space for the blob, in bytes.
* data_size: the size of the blob when decompressed, in bytes. If compression
  is off, it must be equal to used_size.
* Optonal checksum: a single byte 0x00 means no hash, a byte 0xFF means that
  there is, and is followed by a 16-byte md5 hash of the used (compressed) bytes.
* Byte alignment indicator: a uint8 number (0-7) indicating the number of bytes
  to skip before the data starts. 
* Empty space: n empty bytes, as indicated by the byte alignment indicator.
* The binary blob, used_size bytes.
* Empty space, allocated_size - used_size bytes.

TODO: there should be a possibity to end the file with a variable size
block for streaming.
    

### lists

List values consist of the identifier 'l', followed by a size item that represents
the length of the list `n`. After that, `n` values follow, which can be of any
type.

### mappings

Mappings consists of the identifier 'm', followed by a size item that represents
the length of the mapping `n`. After that, `n` items follow, each time a combination of
a string that represents the key (a size + utf-8 encoded string), and the value itself.


## Streaming

Streams allow data to be written and read in a "lazy" fashion. This is
currenly only supported for lists. Objects that are "streaming" must always be
the last object in the file (except for its sub items).

Streams are identified by the size encoding which starts with 255 rather
than 253, followed by an unsigned 64 bit integer. TODO: closed versus
open streams.


## Standard converters

This section specifies a standardised set of converters; a specifification
of how certain objects can be encoded, and how they are named.

This is a work in progress and the specifications below are subject to change.
The standardization of a base set of convertes should settle soonish after the
BSDF format itself has stabalized. BSDF by itself is still useful, as one can
easily define one's own converters. Standardizing the converters is important
to easily share data though.


### Complex numbers 

* name: "c"
* encoding: a list with two elements (the real and the imaginary part).


### N-dimensional arrays

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


