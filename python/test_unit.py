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

import bsdf

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
    
    assert bsdf.lencode(1) == b'\x01'
    assert bsdf.lencode(250) == b'\xfa'
    assert bsdf.lencode(251) == b'\xfd\xfb\x00\x00\x00\x00\x00\x00\x00'
    assert bsdf.lencode(255) == b'\xfd\xff\x00\x00\x00\x00\x00\x00\x00'
    assert bsdf.lencode(256) == b'\xfd\x00\x01\x00\x00\x00\x00\x00\x00'
    assert bsdf.lencode(2**32) == b'\xfd\x00\x00\x00\x00\x01\x00\x00\x00'
    
    assert bsdf.lendecode(io.BytesIO(b'\x01')) == 1
    assert bsdf.lendecode(io.BytesIO(b'\xfa')) == 250
    assert bsdf.lendecode(io.BytesIO(b'\xfd\xfb\x00\x00\x00\x00\x00\x00\x00')) == 251
    assert bsdf.lendecode(io.BytesIO(b'\xfd\xff\x00\x00\x00\x00\x00\x00\x00')) == 255
    assert bsdf.lendecode(io.BytesIO(b'\xfd\x00\x01\x00\x00\x00\x00\x00\x00')) == 256
    assert bsdf.lendecode(io.BytesIO(b'\xfd\x00\x00\x00\x00\x01\x00\x00\x00')) == 2**32


def test_parse_errors():
    
    assert bsdf.decode(b'BSDF\x02\x00v') == None
    assert bsdf.decode(b'BSDF\x02\x00h\x07\x00') == 7
    
    # Not BSDF
    with raises(RuntimeError):
        assert bsdf.decode(b'BZDF\x02\x00v')
    
    # Version mismatch
    with raises(RuntimeError):
        assert bsdf.decode(b'BSDF\x03\x00v')
    with raises(RuntimeError):
        assert bsdf.decode(b'BSDF\x01\x00v')
    
    # Smaller minor version is ok, larger minor version displays warning
    bsdf.decode(b'BSDF\x02\x01v')
    
    # Wrong types
    with raises(RuntimeError):
        bsdf.decode(b'BSDF\x02\x00r\x07')
        #                         \ r is not a known type
    
    
def test_options():
    
    s = bsdf.BsdfSerializer(compression='zlib')
    assert s._compression == 1
    s = bsdf.BsdfSerializer(compression='bz2')
    assert s._compression == 2
    with raises(TypeError):
        bsdf.BsdfSerializer(compression='zzlib')
    with raises(TypeError):
        bsdf.BsdfSerializer(compression=9)


def test_all_types_simple():
    
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
    
    bb = bsdf.encode(s1)
    s2 = bsdf.decode(bb)
    
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
    bb = bsdf.encode(s1)
    s2 = bsdf.decode(bb)
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
    b1 = bsdf.encode(data, compression=0)
    b2 = bsdf.encode(data, compression=1)
    b3 = bsdf.encode(data, compression=2)
    assert len(b1) > 10 * len(b2)
    assert len(b1) > 10 * len(b3)
    
    # Compression can be per-object, using blobs
    data1 = [1, 2, b'\x00' * 10000]
    data2 = [1, 2, bsdf.Blob(b'\x00'  * 10000, compression=1)]
    b1 = bsdf.encode(data1, compression=0)
    b2 = bsdf.encode(data2, compression=0)
    assert len(b1) > 10 * len(b2)
    


def test_float32():
    
    # Using float32 makes smaller files
    data = [2.0, 3.1, 5.1]
    b1 = bsdf.encode(data, float64=False)
    b2 = bsdf.encode(data, float64=True)
    assert len(b1) < len(b2)
    #
    assert bsdf.decode(b1) != data
    assert bsdf.decode(b2) == data
    assert all(abs(i1-i2) < 0.01 for i1, i2 in zip(bsdf.decode(b1), data))
    assert all(abs(i1-i2) < 0.001 for i1, i2 in zip(bsdf.decode(b2), data))
    
    # Does not affect ints
    data = [2, 3, 5]
    b1 = bsdf.encode(data, float64=False)
    b2 = bsdf.encode(data, float64=True)
    assert len(b1) == len(b2)
    #
    assert bsdf.decode(b1) == data
    assert bsdf.decode(b2) == data
    
    # Ints are auto-scaled
    b1 = bsdf.encode([3, 4, 5, 300, 400, 500])
    b2 = bsdf.encode([300000, 400000, 500000, 3000000, 4000000, 5000000])
    assert len(b1) < len(b2)
    #
    assert bsdf.decode(b1) == [3, 4, 5, 300, 400, 500]
    assert bsdf.decode(b2) == [300000, 400000, 500000, 3000000, 4000000, 5000000]


## Extensions


def test_extension_add_remove():
    
    # Not specifying extensions used defaults
    x = bsdf.BsdfSerializer()
    assert len(x._extensions) > 0
    x = bsdf.BsdfSerializer(None)
    assert len(x._extensions) > 0
    
    # Specifying empty list discarts defaults
    x = bsdf.BsdfSerializer([])
    assert len(x._extensions) == 0
    
    class MyExtension(bsdf.Extension):
        name = 'x'
    
    # Add via init or add_extensions()
    x = bsdf.BsdfSerializer([MyExtension])
    assert len(x._extensions) == 1
    x.add_extension(bsdf.ComplexExtension)
    assert len(x._extensions) == 2
    
    # No dups
    x.add_extension(MyExtension)
    x.add_extension(bsdf.ComplexExtension)
    
    # Remove
    with raises(TypeError):
        x.remove_extension(bsdf.ComplexExtension)
    x.remove_extension('x')
    x.remove_extension('c')
    assert len(x._extensions) == 0


def test_standard_extensions_complex():

    x = bsdf.BsdfSerializer()
    
    a = 3 + 4j
    bb = x.encode(a)
    b = x.decode(bb)
    assert a == b


def test_standard_extensions_ndarray():
    
    try:
        import numpy as np
    except ImportError:
        skip('need numpy')
    
    extensions = None
    
    a1 = [1, 2, np.array([1, 2, 3, 4]).reshape((2,2))]
    a2 = [1, 2, np.array([1, 2, 42]*1000)]
    a3 = [1, 2, np.array([4, 2, 42]*1000)]
    b1 = bsdf.encode(a1, extensions)
    b2 = bsdf.encode(a2, extensions, compression=0)
    b3 = bsdf.encode(a3, extensions, compression=1)
    
    assert len(b2) > len(b1) * 10
    assert len(b2) > len(b3) * 10
    
    c1 = bsdf.decode(b1, extensions)
    c2 = bsdf.decode(b2, extensions)
    c3 = bsdf.decode(b3, extensions)
    
    assert np.all(a1[2] == c1[2])
    assert np.all(a2[2] == c2[2])
    assert np.all(a3[2] == c3[2])


def test_custom_extension_array():
    import array
    
    class ArrayExtension(bsdf.Extension):
        name = 'array'
        cls = array.array
        
        def encode(self, arr):
            return dict(typecode=str(arr.typecode),
                        data=arr.tostring())
        def decode(self, d):
            a = array.array(d['typecode'])
            a.fromstring(d['data'])
            return a
    
    extensions = [ArrayExtension]
    
    a1 = [1, 2, array.array('b', [1, 2, 42])]
    a2 = [1, 2, array.array('b', [1, 2, 42]*1000)]
    a3 = [1, 2, array.array('b', [4, 2, 42]*1000)]
    bb1 = bsdf.encode(a1, extensions)
    bb2 = bsdf.encode(a2, extensions, compression=0)
    bb3 = bsdf.encode(a3, extensions, compression=1)
    
    assert len(bb2) > len(bb1) * 10
    assert len(bb2) > len(bb3) * 10
    
    b1 = bsdf.decode(bb1, extensions)
    b2 = bsdf.decode(bb2, extensions)
    b3 = bsdf.decode(bb3, extensions)
    
    assert a1 == b1
    assert a2 == b2
    assert a3 == b3


def test_custom_extensions_fail():
    
    with raises(TypeError):
        bsdf.encode(None, ['not an extension'])
    
    class MyExtension1(bsdf.Extension):
        name = 3
    
    with raises(TypeError):
        bsdf.encode(None, [MyExtension1])
    
    class MyExtension2(bsdf.Extension):
        name = ''
    
    with raises(NameError):
        bsdf.encode(None, [MyExtension2])
    
    class MyExtension3(bsdf.Extension):
        name = 'x' * 1000
    
    with raises(NameError):
        bsdf.encode(None, [MyExtension3])
    
    class MyExtension4(bsdf.Extension):
        name = 'x'
        cls = 4
    
    with raises(TypeError):
        bsdf.encode(None, [MyExtension4])


def test_custom_extensions():
    
    class MyObject1:
        def __init__(self, val):
            self.val = val
        def __repr__(self):
            return '<%s %r>' % (self.__class__.__name__, self.val)
    
    class MyObject2(MyObject1):
        pass
    
    class MyExtension(bsdf.Extension):
        name = 'myob'
        def encode(self, v):
            return v.val
        def decode(self, v):
            return MyObject1(v)
    
    class MyExtension1(MyExtension):
        cls = MyObject1
        def match(self, v):
            return False
    
    class MyExtension2(MyExtension):
        cls = MyObject1, MyObject2
        def match(self, v):
            return False
    
    class MyExtension3(MyExtension):
        cls = MyObject1
        # default: def match(self, v): return isinstance(v, self.cls)
    
    # Define data
    a1 = [1, MyObject1(2), 3]
    a2 = [1, MyObject1(2), MyObject2(3), 4]
    
    # Extension 1 can only encode MyObject1
    b1 = bsdf.encode(a1, [MyExtension1])
    c1 = bsdf.decode(b1, [MyExtension1])
    assert repr(a1) == repr(c1)
    # 
    with raises(TypeError):
        b2 = bsdf.encode(a2, [MyExtension1])
    
    # Extension 2 can encode both
    b1 = bsdf.encode(a1, [MyExtension2])
    c1 = bsdf.decode(b1, [MyExtension2])
    assert repr(a1) == repr(c1)
    #
    b2 = bsdf.encode(a2, [MyExtension2])
    c2 = bsdf.decode(b2, [MyExtension2])
    assert repr(a2).replace('ct2', 'ct1') == repr(c2)
    
    # Extension 3 can encode both too
    b3 = bsdf.encode(a1, [MyExtension2])
    c3 = bsdf.decode(b1, [MyExtension2])
    assert repr(a1) == repr(c1)
    #
    b3 = bsdf.encode(a2, [MyExtension3])
    c3 = bsdf.decode(b2, [MyExtension3])
    assert repr(a2).replace('ct2', 'ct1') == repr(c2)

    # Overwriting works
    b3 = bsdf.encode(a2, [MyExtension1, MyExtension3])
    c3 = bsdf.decode(b2, [MyExtension1, MyExtension3])
    assert repr(a2).replace('ct2', 'ct1') == repr(c2)


## Special implementation stuff - streaming, lazy loading

# todo: better test streaming API
# todo: better test lazy loading and editing blobs in-place

def test_streaming1():
    """ Writing a streamed list. """ 
    f = io.BytesIO()
    
    thelist = bsdf.ListStream()
    a = [3, 4, thelist]
    
    bsdf.save(f, a)
    
    thelist.append('hi')
    for i in range(10):
        thelist.append(i * 101)
    thelist.append((4, 2))
    
    thelist.close()
    bb = f.getvalue()
    b = bsdf.decode(bb)
    
    assert b[-1] == ['hi', 0, 101, 202, 303, 404, 505, 606, 707, 808, 909, [4, 2]]
    
    # Only ListStream
    class MyStream(bsdf.BaseStream):
        pass
    f = io.BytesIO()
    a = [3, 4, MyStream()]
    with raises(TypeError):
        bsdf.save(f, a)
    
    # Only one!
    f = io.BytesIO()
    a = [3, 4, bsdf.ListStream(), bsdf.ListStream()]
    with raises(ValueError):
        bsdf.save(f, a)
    
    # Stream must be at the end
    f = io.BytesIO()
    a = [3, 4, bsdf.ListStream(), 5]
    with raises(ValueError):
        bsdf.save(f, a)


def test_streaming2():
    """ Writing a streamed list, closing the stream. """ 
    f = io.BytesIO()
    
    thelist = bsdf.ListStream()
    a = [3, 4, thelist]
    
    bsdf.save(f, a)
    
    thelist.append('hi')
    
    # closing here will write the length of the stream, marking the stream as closed
    thelist.close()  
    
    for i in range(3):
        thelist.append(i)
    
    bb = f.getvalue()
    b = bsdf.decode(bb)
    
    # However, this BSDF implementation consumes the whole stream anyway
    assert b[-1] == ['hi', 0, 1, 2]


def test_streaming3():
    """ Reading a streamed list. """ 
    f = io.BytesIO()
    
    thelist = bsdf.ListStream()
    a = [3, 4, thelist]
    
    bsdf.save(f, a)
    
    thelist.append('hi')
    for i in range(3):
        thelist.append(i)
    
    bb = f.getvalue()
    b = bsdf.decode(bb, load_streaming=True)
    
    x = b[-1]
    assert isinstance(x, bsdf.ListStream)
    
    x.get_next() == 'a'
    x.get_next() == 0
    x.get_next() == 1
    x.get_next() == 2
    with raises(StopIteration):
        x.get_next()


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
