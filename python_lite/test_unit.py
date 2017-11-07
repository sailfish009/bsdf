"""
Test the main ...
"""

from __future__ import absolute_import, print_function, division

import os
import io
import sys
import array
import tempfile

from pytest import raises

import bsdf_lite

tempfilename = os.path.join(tempfile.gettempdir(), 'bsdf_tests', 'tempfile.bsdf')
if not os.path.isdir(os.path.dirname(tempfilename)):
    os.makedirs(os.path.dirname(tempfilename))


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


## Core tests

def test_length_encoding():

    assert bsdf_lite.lencode(1) == b'\x01'
    assert bsdf_lite.lencode(250) == b'\xfa'
    assert bsdf_lite.lencode(251) == b'\xfd\xfb\x00\x00\x00\x00\x00\x00\x00'
    assert bsdf_lite.lencode(255) == b'\xfd\xff\x00\x00\x00\x00\x00\x00\x00'
    assert bsdf_lite.lencode(256) == b'\xfd\x00\x01\x00\x00\x00\x00\x00\x00'
    assert bsdf_lite.lencode(2**32) == b'\xfd\x00\x00\x00\x00\x01\x00\x00\x00'

    assert bsdf_lite.lendecode(io.BytesIO(b'\x01')) == 1
    assert bsdf_lite.lendecode(io.BytesIO(b'\xfa')) == 250
    assert bsdf_lite.lendecode(io.BytesIO(b'\xfd\xfb\x00\x00\x00\x00\x00\x00\x00')) == 251
    assert bsdf_lite.lendecode(io.BytesIO(b'\xfd\xff\x00\x00\x00\x00\x00\x00\x00')) == 255
    assert bsdf_lite.lendecode(io.BytesIO(b'\xfd\x00\x01\x00\x00\x00\x00\x00\x00')) == 256
    assert bsdf_lite.lendecode(io.BytesIO(b'\xfd\x00\x00\x00\x00\x01\x00\x00\x00')) == 2**32


def test_parse_errors():

    s = bsdf_lite.BsdfLiteSerializer()

    assert s.decode(b'BSDF\x02\x00v') == None
    assert s.decode(b'BSDF\x02\x00h\x07\x00') == 7

    # Not BSDF
    with raises(RuntimeError):
        assert s.decode(b'BZDF\x02\x00v')

    # Version mismatch
    with raises(RuntimeError):
        assert s.decode(b'BSDF\x03\x00v')
    with raises(RuntimeError):
        assert s.decode(b'BSDF\x01\x00v')

    # Smaller minor version is ok, larger minor version displays warning
    s.decode(b'BSDF\x02\x01v')

    # Wrong types
    with raises(RuntimeError):
        s.decode(b'BSDF\x02\x00r\x07')
        #                         \ r is not a known type


def test_options():

    s = bsdf_lite.BsdfLiteSerializer(compression='zlib')
    assert s._compression == 1
    s = bsdf_lite.BsdfLiteSerializer(compression='bz2')
    assert s._compression == 2
    with raises(TypeError):
        bsdf_lite.BsdfLiteSerializer(compression='zzlib')
    with raises(TypeError):
        bsdf_lite.BsdfLiteSerializer(compression=9)


def test_all_types_simple():
    s = bsdf_lite.BsdfLiteSerializer()

    s1 = dict(v1 = None,
              v2 = False,
              v3 = True,
              v4 = 3,
              v5 = 3.2,
              v6 = u'a',  # u-prefix is needed in Legacy Python to not be bytes
              v7 = u'aa',
              v8 = (1, 2),
              v9 = [3, 4],
              v10 = {'a': 0, 'b': 1},
              v11 = b'b',
              v12 = b'bb',
             )

    bb = s.encode(s1)
    s2 = s.decode(bb)

    # Correction - tuples become lists
    assert isinstance(s2['v8'], list)
    s2['v8'] = tuple(s2['v8'])

    assert bb.startswith(b'BSDF')
    assert s1 == s2
    for key in s1:
        assert type(s1[key]) == type(s2[key])


def test_loaders_and_savers_of_serializer():

    s1 = dict(foo=42, bar=[1, 2.1, False, 'spam', b'eggs'])

    serializer = bsdf_lite.BsdfLiteSerializer()

    # In-memory
    bb = serializer.encode(s1)
    s2 = serializer.decode(bb)
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


def test_compression():

    # Compressing makes smaller files
    data = [1, 2, b'\x00' * 10000]
    b1 = bsdf_lite.BsdfLiteSerializer(compression=0).encode(data)
    b2 = bsdf_lite.BsdfLiteSerializer(compression=1).encode(data)
    b3 = bsdf_lite.BsdfLiteSerializer(compression=2).encode(data)
    assert len(b1) > 10 * len(b2)
    assert len(b1) > 10 * len(b3)


def test_float32():
    s = bsdf_lite.BsdfLiteSerializer()

    # Using float32 makes smaller files
    data = [2.0, 3.1, 5.1]
    b1 = bsdf_lite.BsdfLiteSerializer(float64=False).encode(data)
    b2 = bsdf_lite.BsdfLiteSerializer(float64=True).encode(data)
    assert len(b1) < len(b2)
    #
    assert s.decode(b1) != data
    assert s.decode(b2) == data
    assert all(abs(i1-i2) < 0.01 for i1, i2 in zip(s.decode(b1), data))
    assert all(abs(i1-i2) < 0.001 for i1, i2 in zip(s.decode(b2), data))

    # Does not affect ints
    data = [2, 3, 5]
    b1 = bsdf_lite.BsdfLiteSerializer(float64=False).encode(data)
    b2 = bsdf_lite.BsdfLiteSerializer(float64=True).encode(data)
    assert len(b1) == len(b2)
    #
    assert s.decode(b1) == data
    assert s.decode(b2) == data

    # Ints are auto-scaled
    b1 = s.encode([3, 4, 5])
    b2 = s.encode([300000, 400000, 500000])
    assert len(b1) < len(b2)
    #
    assert s.decode(b1) == [3, 4, 5]
    assert s.decode(b2) == [300000, 400000, 500000]


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
