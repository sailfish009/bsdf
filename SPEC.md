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
* Two variable size unsigned integers indicating major and minor version
  numbers. Currently 2 and 0.
* 1 or 9 bytes: size of converter names block.
* the data
* N strings (see below) of converter names.
* end blob

Each data value is identified using a 1 byte character, followed by an optional
converted index, and the data (if applicable).

If the identifier is a capital letter (smaller than ASCII 95), it means
that it's a value to be converted. If so, the next item is a size (1
or 9 bytes) representing the converter index.

### Encoding of size

The size of lists, mappings and the number of elements in the converter block
are encoded as follows: if the size is smaller than 255, a single byte (uint8)
is used. Otherwise, the first byte is 255, and the next 8 bytes represent
the size using a 64bit float.

It might seem odd to use a floating point number to represent an
integer. The reason is that not all languages support 64 bit numbers ...
mmmm but we can do some bitshifting and whatnot to make it work...

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
