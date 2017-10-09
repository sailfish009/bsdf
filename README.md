<a href="https://gitlab.com/almarklein/bsdf/pipelines">
<img alt="pipeline status" align='right' src="https://gitlab.com/almarklein/bsdf/badges/master/pipeline.svg" />
</a>

<a class='badge' href='http://almarklein.gitlab.io/bsdf'>Website / docs</a>
<span class='badge_sep'>|</span>
<a class='badge' href='http://gitlab.com/almarklein/bsdf'>Gitlab / source code</a>


# Binary Structured Data Format

The Binary Structured Data Format (BSDF) is an open specification for
serializing (scientific) data, for the purpose of storage and (inter process)
communication.

It's designed to be a simple format, making it easy to implement in
many programming languages. However, the format allows implementations
to support powerful mechanics such as lazy loading of binary data, and
streamed reading/writing.

## Format

BSDF supports 8 base types: null, booleans, integers, floats, strings/text,
(heterogenous) lists, mappings (i.e. dictionaries), and binary blobs. Integers
and floats represent 64 bit numbers, but can be encoded using less
bytes. Binary blobs can optionally be compressed (zlib or bz2), can have
checksums, and can be resized. BSDF has an efficient extension mechanism
by which other types of data can be serialized with user-defined
converter functions.

BSDF is a binary format; by giving up on human readability, we were able to
make BSDF simple, compact and fast. See the [full specification](SPEC.md), or
how it [compares](COMPARISON.md) to other formats.


## Implementations

* The [Python implementation](py) in the form of [bsdf.py](py/bsdf.py).
* The [Matlab / Octave implementation](matlab) in the form of [bsdf.m](matlab/bsdf.m).
* The [JavaScript implementation](js) (WIP) in the form of [bsdf.js](js/bsdf.js).

Implementations for other languages are planned. BSDF is designed to be easy
to implement; perhaps you want to contribute?


## Development

Since BSDF is designed to be simple, implementations are usually
restricted to a single module. The BSDF Gitlab repo contains
implementations for several languages, organized in sub directories.
This allows testing each implementation using a "test service", and ensures
compatibility between the different implementations.

The tooling around BSDF is implemented in Python. For development, you
need Python 3.x and the invoke library (`pip install invoke`).

To run tasks such as tests, run `invoke` from the root repo to get started.
