<a href="https://gitlab.com/almarklein/bsdf/commits/master">
<img alt="pipeline status" align='right' src="https://gitlab.com/almarklein/bsdf/badges/master/pipeline.svg" />
</a>

<a class='badge' href='http://almarklein.gitlab.io/bsdf'>Website / docs</a>
<span class='badge_sep'>|</span>
<a class='badge' href='http://gitlab.com/almarklein/bsdf'>Gitlab repo</a>


# Binary Structured Data Format

The Binary Structured Data Format (BSDF) is an open specification for
serializing (scientific) data, with implementations in several
languages.

Note: these docs are a work in progress ...


## Implementations

* The [Python implementation](py) in the form of [bsdf.py](py/bsdf.py).
* The [Matlab / Octave implementation](matlab) in the form of [bsdf.m](matlab/bsdf.m).
* The [JavaScript implementation](js) (WIP) in the form of [bsdf.js](js/bsdf.js).

Implementations for other languages are planned. BSDF is designed to be easy
to implement; perhaps you want to contribute?


## Specification

BSDF is designed to be simple; the [full specification](SPEC.md) is quite short.

A minimal BSDF implementation must suport:

* the basic data types: null, bool, int, float, string, list, map/dict.
* uncompressed binary blobs.
* unclosed streams (at the end of a data structure).
* preferably most standard converters.

Implementations are encouraged to support:

* user-defined converters.
* compressed binary blobs (zlib and bz2).

Further implementations can be made more powerful by supporting:

* Lazy loading of blobs.
* Lazy loading of streams.
* Deferred writing of streams.


## Development

Since BSDF is designed to be simple, implementations are usually
restricted to a single module. The BSDF Gitlab repo contains
implementations for several languages, organized in sub directories.
This allows testing each implementation using a "test service", and ensures
compatibility between the different implementations.

The tooling around BSDF is implemented in Python. For development, you
need Python 3.x and the invoke library (`pip install invoke`).

To run tasks such as tests, run `invoke` from the root repo to get started.
