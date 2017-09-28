# BSDF Python implementation

This is the reference implementation of BSDF, and this directory also
contains script to help test other BSDF implementations, most notably
bsdf_test_service.py.


## Installation

At this point, copy `bsdf.py` to a place where Python can find it.


## Running tests

(In the commands below, the `.` can be replaced with `py` when running from
the root of the repository.)

* Style tests: `flake8 .`
* Unit tests: `pytest .`
* Service tests: `python ./bsdf_test_service.py python .`


## Maintainers

* @almarklein
