# Copyright (c) 2011-2017, Almar Klein

"""
Create random dictionaries.
"""

import os
import time
import sys
import random
import string
import numpy as np

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


names = set()
def random_name(maxn=32):
    name = ''
    while not (name and name not in names):
        n = random.randrange(0, maxn)
        name = random.choice(NAMECHARS[:-10])
        name += ''.join(random.sample(NAMECHARS,n))
        if name.startswith('__'):
            name = 'x' + name
    return name

def random_object(level, types=()):
    
    # Get what types are allowed
    M = {'None': 1, 'bool': 2, 'int': 3, 'float': 4, 'str': 5, 'array': 6,
         'list': 7, 'dict': 8}
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
        return None  # random_array()
    elif id == 7:
        return random_list(level, types=types)
    elif id == 8:
        return random_dict(level, types=types)

def random_bool():
    return random.random() > 0.5

def random_int():
    return random.randint(-2**62, 2**62)

def random_float():
    # todo: add nan and inf, but carefull; I test some things against JSON,
    # which does not support these
    return (random.random()-0.5 ) * 10000

def random_string(maxn=16):
    n = random.randrange(0, maxn)
    return ''.join(random.sample(CHARS,n))

def random_array(maxn=16):
    # Get array properties
    ndim = random.randrange(0, 4)
    shape = random.sample(xrange(maxn), ndim)
    dtype = random.choice() # todo: xx
    # Create array
    if 'int' in dtype:
        return np.random.random_integers(0,100, shape).astype(dtype)
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
    if random.random() > 0.5:
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
    
    #print(random_dict())
    print(random_dict(8, 17, 17, ['dict', 'int']))
