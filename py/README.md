# BSDF Python implementation

This is the reference implementation of BSDF, with support for streamed
reading and writing, and lazy loading of binary blobs.

This directory also contains tooling to help test other BSDF
implementations, most notably bsdf_test_service.py.


## Installation

At this point, copy [bsdf.py](bsdf.py) to a place where Python can find it.
There are no dependencies except Python 2.7 or Python 3.4+.


## Development

Run `invoke -l` in this directory for available tasks (like tests).


## Maintainers

* @almarklein
