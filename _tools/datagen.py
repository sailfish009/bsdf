# Copyright (c) 2011-2017, Almar Klein

"""
Module for creating random dictionaries. When run as a script, popluates
the directory with random (though repeatable) data structures.
"""

import os
import sys
import time
import json
import random
import string
from io import open


# From six.py
PY3 = sys.version_info[0] == 3
if PY3:
    string_types = str,
    text_type = str
    binary_type = bytes
    ascii_type = str # Simple string
    unichr = chr
    xrange = range
else:
    string_types = basestring,
    text_type = unicode
    binary_type = str
    ascii_type = str # Simple string

# Get printabel chars, add some Unicode characters
CHARS = string.printable + (unichr(169) + unichr(181) + unichr(202) + 
                            unichr(1220) + unichr(1138) + unichr(1297))
NAMECHARS = str('abcdefghijklmnopqrstuvwxyz_0123456789')

JSON_TYPES = ('null', 'bool', 'int', 'float', 'str', 'list', 'dict')
ALL_TYPES = JSON_TYPES + ('notfinite', 'ndarray')


names = set()
def random_name(maxn=32):
    name = ''
    while not (name and name not in names):
        n = random.randrange(0, maxn)
        name = random.choice(NAMECHARS[:-11])
        name += ''.join(random.sample(NAMECHARS,n))
        assert name[0] not in '_0123456789'
    return name

def random_object(level, types=()):
    
    # Get what types are allowed
    M = {'null': 1, 'bool': 2, 'int': 3, 'float': 4, 'str': 5, 'ndarray': 6,
         'list': 7, 'dict': 8, 'notfinite': 9}
    if types:
        assert all(t in M for t in types)
        allowed_ids = [M[key] for key in types]
    else:
        allowed_ids = (1, 2, 3, 4, 5, 6, 7, 8)
    if level <= 0:
        allowed_ids = [i for i in allowed_ids if i < 7]  # not too deep
    assert allowed_ids
    
    # Select
    id = random.sample(allowed_ids, 1)[0]
    
    if id == 1:
        return None
    elif id == 2:
        return random_bool()
    elif id == 3:
        return random_int()
    elif id == 4:
        return random_float()
    elif id == 5:
        return random_string()
    elif id == 6:
        return random_ndarray()
    elif id == 7:
        return random_list(level, types=types)
    elif id == 8:
        return random_dict(level, types=types)
    elif id == 9:
        return random.sample([float(x) for x in ('nan', '+inf', '-inf')], 1)[0]
    else:
        assert False

def random_bool():
    return random.random() > 0.5

def random_int():
    # Range based on maxiumum that can be reliably encoded with a float64, since
    # some languages (e.g. JS) don't have real ints.
    return random.randint(-9007199254740991, 9007199254740991)

def random_float():
    # which does not support these
    return (random.random()-0.5 ) * 10000

def random_string(maxn=16):
    n = random.randrange(0, maxn)
    return ''.join(random.sample(CHARS,n))

def random_ndarray(maxn=16):
    import numpy as np
    # Get array properties
    shape = (1,)
    while np.prod(shape) == 1:
        ndim = random.randrange(1, 5)  # don't allow empty shape (i.e. weird scalars)
        shape = random.sample(xrange(maxn), ndim)
    dtype = random.choice(['int8', 'uint16', 'int32', 'float32'])
    # Create array
    if 'int' in dtype:
        return np.random.random_integers(0, 100, shape).astype(dtype)
    else:
        return np.random.random_sample(shape).astype(dtype)

def random_list(level, maxn=16, types=()):
    level -= 1
    # Create list and amount of elements
    items = []
    n = random.randrange(0, maxn)
    # Fill
    for i in range(n):
        # Get value
        items.append(random_object(level, types) )
    if True: # random.random() > 0.5: -> this would break comparisons
        return items
    else:
        return tuple(items)

def random_dict(level=8, minn=0, maxn=16, types=()):
    level -= 1
    # Create struct and amount of elements
    s = {}
    n = random.randrange(minn, maxn+1)
    # Fill
    for i in range(n):
        name = random_name()
        s[name] = random_object(level, types)
    if random.random() > 0.5:
        return s
    else:
        return dict(s)


if __name__ == '__main__':
    
    # JSON compatible structures in three sizes
    random.seed('4001')
    d = random_dict(3, 500, 500, types=JSON_TYPES)
    with open('rand01.json', 'wt', encoding='utf-8') as f:
        json.dump(d, f)
    #
    random.seed('4002')
    d = random_dict(4, 1000, 1000, types=JSON_TYPES)
    with open('rand02.json', 'wt', encoding='utf-8') as f:
        json.dump(d, f)
    #
    random.seed('4003')
    d = random_dict(5, 9000, 9000, types=JSON_TYPES)
    with open('rand03.json', 'wt', encoding='utf-8') as f:
        json.dump(d, f)
    
    # A structure only of dicts and null, to test performance of core alg
    random.seed('4004')
    d = random_dict(4, 1000, 1000, types=('null', 'dict'))
    with open('rand04_nulldict.json', 'wt', encoding='utf-8') as f:
        json.dump(d, f)
    
    # A structure only of lists and null, to test performance of core alg
    random.seed('4005')
    d = random_dict(4, 1000, 1000, types=('null', 'list'))
    with open('rand05_nulllist.json', 'wt', encoding='utf-8') as f:
        json.dump(d, f)
    
    # Create corresponding js files to test in browser
    for fname in os.listdir('.'):
        if fname.endswith('.json'):
            with open(fname[:-4] + 'js', 'wt', encoding='utf-8') as f:
                f.write(fname[:-5] + '=')
                f.write(open(fname, 'rt', encoding='utf-8').read())
                f.write(';')
