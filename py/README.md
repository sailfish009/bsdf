# BSDF Python implementation

This is the reference implementation of BSDF, and this directory also
contains script to help test other BSDF implementations, most notably
bsdf_test_service.py.


## Installation

At this point, copy `bsdf.py` to a place where Python can find it.


## Running tests

(Assuming that the current directory is the root of the repo.)

* Style tests: `flake8 py`
* Unit tests: `pytest py`
* Service tests: `python py/bsdf_test_service.py py python`


## Maintainers

* @almarklein
