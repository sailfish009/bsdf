# BSDF

Binary Structured Data Format

## Introduction


## Installation

Differs per implementation, but in general the `bsdf.xx` file can be included
in your project.


## Implementations

* The [Python implementation](py) in the form of [bsdf.py](bsdf.py).
* The [Matlab / Octave implementation](matlab) in the form of [bsdf.m](bsdf.m).
* The [JavaScript implementation](js) in the form of [bsdf.js](bsdf.js).


## Minimal BSDF implementation

A minimal BSDF implementation must suport:

* the basic data types: null, bool, int, float, string, list, map/dict.
* uncompressed binary blobs.
* unclosed streams (at the end of a data structure).
* all standard converters.

Implementations are encouraged to support:

* user-defined converters.
* compressed binary blobs (zlib and bz2).

Further implementations can be made more powerful by supporting:

* Lazy loading of blobs.
* Lazy loading of streams.
* Deferred writing of streams.


## Development

Since BSDF is designed to be simple, implementations are usually restricted
to a single module. This repo contains all "official" implementations,
organized in sub directories. This also makes it easier to test each
implementation using a "test service".

The tooling around BSDF is implemented in Python. For development, you
need Python 3.x and the invoke library (`pip install invoke`).

To run tests and run other tasks, run `invoke` from the root repo to
get started.

