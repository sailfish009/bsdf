"""
Script to benchmark the Python implementation of BSDF (and other
formats) against JSON.

Note that JSON is partly implemented in C from Python 3.x.
"""

import os
import sys
import json
import random
import string
from time import perf_counter
#from time import time as perf_counter  # legacy py

from generate import random_dict

# === BSDF
import bsdf as lib

# === YAML
# import yaml as lib
# import io
# lib.loads = lambda bb: lib.load(io.StringIO(bb))
# lib.dumps = lib.dump

# === msgpack
# # os.environ['MSGPACK_PUREPYTHON'] = '1'
# import msgpack as lib
# lib.dumps = lib.packb
# lib.loads = lib.unpackb


TYPES = 'None', 'bool', 'int', 'float', 'dict', 'list', 'str'

def timeit(func, arg):
    t0 = perf_counter()
    res = func(arg)
    t1 = perf_counter()
    return res, int((t1 - t0) * 1000)


## Small ramdom dict for show

d0 = d = random_dict(3, 7, 7, TYPES)
d['aaaa'] = float('inf')
d['aaab'] = float('nan')
# d['x'] = list(range(100))

print('----')
print(d)
print('----')
print(json.dumps(d))
print('----')
print(lib.dumps(d))


## Encode / decode

d = random_dict(3, 10000, 10000, TYPES)

r1, t1 = timeit(json.dumps, d)
r2, t2 = timeit(lib.dumps, d)

print('encoding:', t1, t2, int(100*t1/t2), '%' )

d1, t1 = timeit(json.loads, r1)
d2, t2 = timeit(lib.loads, r2)

print('decoding', t1, t2, int(100*t1/t2), '%' )


print(len(str(d1)), len(str(d2)))
print('%0.0f%%' % (100*len(r2)/len(r1)))
print('equal:', d1 == d2)
