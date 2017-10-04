"""
Script to benchmark the Python implementation of BSDF (and other
formats) against JSON.

Note that JSON is partly implemented in C from Python 3.x, giving it a
significant performance advantage. One can expect an equally large performance
boost if BSDF is ever implemented in C. For now, let's try to get it more or
less in the same order of magnitude.
"""

import os
import sys
import json
from time import perf_counter, sleep
#from time import time as perf_counter  # legacy py


# === BSDF
import bsdf
lib = bsdf.BsdfSerializer()
lib.dumps = lib.saves

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


TYPES = 'None', 'bool', 'int', 'float', 'str', 'dict', 'list'


def timeit(func, arg, n=1, **kwargs):
    t0 = perf_counter()
    for i in range(n):
        res = func(arg, **kwargs)
    t1 = perf_counter()
    return res, int((t1 - t0) * 1000)


for fname, n in [('rand01', 100),
                 ('rand02', 10),
                 ('rand03', 1),
                 ('rand04_nulldict', 2),
                 ('rand05_nulllist', 4)
                 ]:
    print('-' * 10 + ' ' + fname + ' ' + str(n))
    d = json.load(open('../_data/%s.json' % fname, 'rt', encoding='utf-8'))
    
    r1, t1 = timeit(json.dumps, d)
    r2, t2 = timeit(lib.dumps, d, n)
    
    print('encoding:', t1, t2, int(100*t1/t2), '%' )
    
    d1, t1 = timeit(json.loads, r1, n)
    d2, t2 = timeit(lib.loads, r2, n)
    
    print('decoding', t1, t2, int(100*t1/t2), '%' )
    
    
    print(len(str(d1)), len(str(d2)))
    print('%0.0f%%' % (100*len(r2)/len(r1)))
    print('equal:', d1 == d2)
