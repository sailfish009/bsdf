"""
Test the main ...
"""

import os

from pytest import raises

import bsdf


tempfilename = os.path.join(bsdf.__file__, '..', '..', 'data', 'tempfile.bsdf')
tempfilename = os.path.abspath(tempfilename)


class StrictReadFile:
    """ A file object that has little methods, matching e.g. urlopen(). """
    
    def __init__(self, f):
        self.f = f
    
    def read(self, n):
        return self.f.read(n)


class StrictWriteFile(StrictReadFile):
    """ A file object that has little methods. """
    
    def write(self, bb):
        return self.f.write(bb)
    
    def tell(self):
        return self.f.tell()


def test_all_types_simple():
    
    s1 = dict(v1 = None,
              v2 = False,
              v3 = True,
              v4 = 3,
              v5 = 3.2,
              v6 = 'a',
              v7 = 'aa',
              v8 = (1, 2),
              v9 = [3, 4],
              v10 = {'a': 0, 'b': 1},
              v11 = b'a',
              v12 = b'aa',
             )
    
    bb = bsdf.saves(s1)
    s2 = bsdf.loads(bb)
    
    # Correction - tuples become lists
    assert isinstance(s2['v8'], list)
    s2['v8'] = tuple(s2['v8'])
    
    assert bb.startswith(b'BSDF')
    assert s1 == s2
    for key in s1:
        assert type(s1[key]) == type(s2[key])

def test_loaders_and_savers():
    
    # load and save is already tested above and in many other places
    
    s1 = dict(foo=42, bar=[1, 2.1, False, 'spam', b'eggs'])
    
    # In-memory
    bb = bsdf.saves(s1)
    s2 = bsdf.loads(bb)
    assert s1 == s2
    
    # Using a filename
    bsdf.save(tempfilename, s1)
    s2 = bsdf.load(tempfilename)
    assert s1 == s2
    
    # Using a file object
    with open(tempfilename, 'wb') as f:
        bsdf.save(f, s1)
    with open(tempfilename, 'rb') as f:
        s2 = bsdf.load(f)
    assert s1 == s2
    
    # Using a very strict file object
    with open(tempfilename, 'wb') as f:
        bsdf.save(StrictWriteFile(f), s1)
    with open(tempfilename, 'rb') as f:
        s2 = bsdf.load(StrictReadFile(f))
    assert s1 == s2


def test_loaders_and_savers_of_serializer():
    
    s1 = dict(foo=42, bar=[1, 2.1, False, 'spam', b'eggs'])
    
    serializer = bsdf.BsdfSerializer()
    
    # In-memory
    bb = serializer.saves(s1)
    s2 = serializer.loads(bb)
    assert s1 == s2
    
    # Using a filename fails
    with raises(AttributeError):
        serializer.save(tempfilename, s1)
    with raises(AttributeError):
        s2 = serializer.load(tempfilename)
    
    # Using a file object
    with open(tempfilename, 'wb') as f:
        serializer.save(f, s1)
    with open(tempfilename, 'rb') as f:
        s2 = serializer.load(f)
    assert s1 == s2
    
    # Using a very strict file object
    with open(tempfilename, 'wb') as f:
        serializer.save(StrictWriteFile(f), s1)
    with open(tempfilename, 'rb') as f:
        s2 = serializer.load(StrictReadFile(f))
    assert s1 == s2


def test_encode_complex():

    complex_conv = 'complex', complex, lambda ctx, c: (c.real, c.imag), lambda ctx, v: complex(*v)
    x = bsdf.BsdfSerializer(complex_conv)
    
    a = 3 + 4j
    bb = x.saves(a)
    b = x.loads(bb)
    assert a == b


def test_encode_array():
    import array
    
    def array_encode(ctx, arr):
        return dict(typecode=str(arr.typecode),
                    data=arr.tobytes())
    
    def array_decode(ctx, d):
        a = array.array(d['typecode'])
        a.frombytes(d['data'])
        return a
    
    converters = [('test_array', array.array, array_encode, array_decode)]
    
    a1 = [1, 2, array.array('b', [1, 2, 42])]
    a2 = [1, 2, array.array('b', [1, 2, 42]*1000)]
    a3 = [1, 2, array.array('b', [4, 2, 42]*1000)]
    bb1 = bsdf.saves(a1, converters)
    bb2 = bsdf.saves(a2, converters, compression=0)
    bb3 = bsdf.saves(a3, converters, compression=2)
    
    assert len(bb2) > len(bb1) * 10
    assert len(bb2) > len(bb3) * 10
    
    b1 = bsdf.loads(bb1, converters)
    b2 = bsdf.loads(bb2, converters)
    b3 = bsdf.loads(bb3, converters)
    
    assert a1 == b1
    assert a2 == b2
    assert a3 == b3


if __name__ == '__main__':
    
    for name, func in list(globals().items()):
        if name.startswith('test_'):
            print('Running %s ' % name, end='')
            try:
                func()
            except Exception:
                print('  Failed')
                raise
            print('  Passed')
