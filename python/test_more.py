"""
Test the more advanced features of this BSDF implementation,
such as streaming and lazy loading.
"""


from __future__ import absolute_import, print_function, division

import os
import io
import sys
import array
import tempfile

from pytest import raises, skip

import bsdf

tempfilename = os.path.join(tempfile.gettempdir(), 'bsdf_tests', 'tempfile.bsdf')
if not os.path.isdir(os.path.dirname(tempfilename)):
    os.makedirs(os.path.dirname(tempfilename))


## Streaming


def test_liststreaming1():
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


def test_liststreaming_write_fails():
    
    # Only write mode
    f = io.BytesIO()
    ls = bsdf.ListStream('r')
    with raises(ValueError):
        bsdf.save(f, ls)
    with raises(IOError):
        ls.append(3)
    with raises(IOError):
        ls.close()
    
    # Dont append (or close) before use
    ls = bsdf.ListStream()
    with raises(IOError):
        ls.append(3)
    with raises(IOError):
        ls.close()
    
    # Only use once!
    f = io.BytesIO()
    ls = bsdf.ListStream()
    bsdf.save(f, ls)
    with raises(IOError):
        bsdf.save(f, ls)
    
    # Do not write when closed!
    f = io.BytesIO()
    ls = bsdf.ListStream()
    bsdf.save(f, ls)
    f.close()
    with raises(IOError):
        ls.append(3)
    with raises(IOError):
        ls.close()
    
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


def test_streaming_closing123():
    """ Writing a streamed list, closing the stream. """
    for iter in range(4):
        
        f = io.BytesIO()
    
        thelist = bsdf.ListStream()
        bsdf.save(f, thelist)
    
        thelist.append('hi')
    
        # closing here will write the length of the stream, marking the stream as closed
        if iter in (1, 2):
            thelist.close()
    
        for i in range(3):
            thelist.append(i)
        
        if iter == 2:
            thelist.close()
        if iter == 3:
            thelist.close(True)
        
        assert thelist.count == 4
        assert thelist.index == thelist.count
        
        bb = f.getvalue()
        b1 = bsdf.decode(bb)
        b2 = bsdf.decode(bb, load_streaming=True)
        
        if iter in (0, 1, 2):
            assert isinstance(b2, bsdf.ListStream) and not isinstance(b2, list)
        else:
            assert not isinstance(b2, bsdf.ListStream) and isinstance(b2, list)
        
        if iter == 0:
            # Not closed
            assert b1 == ['hi', 0, 1, 2]
            assert list(b2) == ['hi', 0, 1, 2]
        elif iter == 1:
            # Closed, and elements added later
            assert b1 == ['hi']
            assert list(b2) == ['hi']
        elif iter == 2:
            # Closed twice
            assert b1 == ['hi', 0, 1, 2]
            assert list(b2) == ['hi', 0, 1, 2]
        elif iter == 3:
            # Closed twice
            assert b1 == ['hi', 0, 1, 2]
            assert list(b2) == ['hi', 0, 1, 2]
        else:
            assert False


def test_liststreaming_reading1():
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

    assert x.next() == 'hi'
    assert x.next() == 0
    assert x.next() == 1
    assert x.next() == 2
    with raises(StopIteration):
        x.next()
    
    # Support iteration
    b = bsdf.decode(bb, load_streaming=True)
    x = b[-1]
    xx = [i for i in x]
    assert xx == ['hi', 0, 1, 2]
    
    # Cannot read after file is closed
    f = io.BytesIO(bb)
    b = bsdf.load(f, load_streaming=True)
    x = b[-1]
    f.close()
    with raises(IOError):
        x.next()
    
    # Cannot read when in read-mode
    ls = bsdf.ListStream()
    with raises(IOError):
        ls.next()
    with raises(IOError):
        list(ls)
    
    # mmm, this would never happen, I guess, but need associated file!
    ls = bsdf.ListStream('r')
    with raises(IOError):
        ls.next()


def test_liststream_modding():
    
    # Create a file
    ls = bsdf.ListStream()
    with open(tempfilename, 'wb') as f:
        bsdf.save(f, ls)
        ls.append('foo')
        ls.append('bar')
    
    assert bsdf.load(tempfilename) == ['foo', 'bar']
    
    # Append items hard-core more
    with open(tempfilename, 'ab') as f:
        f.write(b'v')
        f.write(b'h*\x00')  # ord('*') == 42
    
    assert bsdf.load(tempfilename) == ['foo', 'bar', None, 42]
    
    # Append items using the BSDF API
    with open(tempfilename, 'r+b') as f:
        ls = bsdf.load(f, load_streaming=True)
        for i in ls:
            pass
        ls.append(4)
        ls.append(5)
        ls.close()  # also close here
    
    assert bsdf.load(tempfilename) == ['foo', 'bar', None, 42, 4, 5]
    
    # Try adding more items
    with open(tempfilename, 'ab') as f:
        f.write(b'v')
        f.write(b'h*\x00')  # ord('*') == 42
    
    # But no effect
    assert bsdf.load(tempfilename) == ['foo', 'bar', None, 42, 4, 5]


## Blobs

def test_blob_writing1():
    
    # Use blob to specify bytes
    blob = bsdf.Blob(b'xxxx')
    bb1 = bsdf.encode([2, 3, blob, 5])
    
    # Again, with extra size
    blob = bsdf.Blob(b'xxxx', extra_size=100)
    bb2 = bsdf.encode([2, 3, blob, 5])
    
    # Again, with checksum
    blob = bsdf.Blob(b'xxxx', use_checksum=True)
    bb3 = bsdf.encode([2, 3, blob, 5])
    
    
    assert len(bb2) == len(bb1) + 100
    assert len(bb3) == len(bb1) + 16
    
    assert bsdf.decode(bb1) == [2, 3, b'xxxx', 5]
    assert bsdf.decode(bb2) == [2, 3, b'xxxx', 5]
    assert bsdf.decode(bb3) == [2, 3, b'xxxx', 5]

    # Fail
    with raises(TypeError):
        bsdf.Blob([1, 2, 3])
    with raises(RuntimeError):
        blob.tell()
    with raises(RuntimeError):
        blob.seek(0)
    with raises(RuntimeError):
        blob.read(1)
    with raises(RuntimeError):
        blob.write(b'xx')


def test_blob_reading1():
    
    blob = bsdf.Blob(b'xxxx')
    bb1 = bsdf.encode([2, 3, blob, 5])
    
    res1 = bsdf.decode(bb1)
    assert isinstance(res1[2], bytes)
    
    res1 = bsdf.decode(bb1, lazy_blob=True)
    assert not isinstance(res1[2], bytes) and isinstance(res1[2], bsdf.Blob)
    
    res1[2].get_bytes() == b'xxxx'


def test_blob_reading2():
    bb = bsdf.encode(bsdf.Blob(b'xxyyzz', extra_size=2))
    f = io.BytesIO(bb)
    blob = bsdf.load(f, lazy_blob=True)
    
    # Always seek first
    blob.seek(0)
    assert blob.read(2) == b'xx'
    assert blob.tell() == 2
    assert blob.read(2) == b'yy'
    
    # We can overwrite, but changes an internal file that we cannot use :P
    blob.write(b'aa')
    
    blob.seek(0)
    assert blob.read(2) == b'xx'
    
    blob.seek(-2) # relative to allocated size
    assert blob.tell() == 6
    
    # can just about do this, due to extra size
    blob.seek(8)
    # But this is too far
    with raises(IOError):
        blob.seek(9)
    # And so is this
    blob.seek(6)
    with raises(IOError):
        blob.write(b'xxx')
    # And this
    blob.seek(6)
    with raises(IOError):
        blob.read(3)


def test_blob_reading3():  # compression
    # ZLib
    bb = bsdf.encode(bsdf.Blob(b'xxyyzz', compression=1))
    f = io.BytesIO(bb)
    blob = bsdf.load(f, lazy_blob=True)
    #
    blob.get_bytes() == b'xxyyzz'
    
    # BZ2
    bb = bsdf.encode(bsdf.Blob(b'xxyyzz', compression=2))
    f = io.BytesIO(bb)
    blob = bsdf.load(f, lazy_blob=True)
    #
    blob.get_bytes() == b'xxyyzz'
    
    # But we cannot read or write
    blob.seek(0)
    with raises(IOError):
        blob.read(2)
    with raises(IOError):
        blob.write(b'aa')


def test_blob_modding1():  # plain
    
    bb = bsdf.encode(bsdf.Blob(b'xxyyzz', extra_size=2))
    f = io.BytesIO(bb)
    blob = bsdf.load(f, lazy_blob=True)
    
    blob.seek(4)
    blob.write(b'aa')
    blob.update_checksum()
    assert bsdf.decode(f.getvalue()) == b'xxyyaa'


def test_blob_modding2():  # with checksum
    
    bb = bsdf.encode(bsdf.Blob(b'xxyyzz', extra_size=2, use_checksum=True))
    f = io.BytesIO(bb)
    blob = bsdf.load(f, lazy_blob=True)
    
    blob.seek(4)
    blob.write(b'aa')
    blob.update_checksum()
    assert bsdf.decode(f.getvalue()) == b'xxyyaa'


def test_blob_modding3():  # actual files
    bsdf.save(tempfilename, bsdf.Blob(b'xxyyzz', extra_size=2))
    
    # Can read, but not modify in rb mode
    with open(tempfilename, 'rb') as f:
        blob = bsdf.load(f, lazy_blob=True)
        
        blob.seek(0)
        assert blob.read(2) == b'xx'
        blob.seek(4)
        with raises(IOError):
            blob.write(b'aa')
    
    # But we can in a+ mode
    with open(tempfilename, 'r+b') as f:
        blob = bsdf.load(f, lazy_blob=True)
        
        blob.seek(0)
        assert blob.read(2) == b'xx'
        blob.seek(4)
        blob.write(b'aa')
    
    assert bsdf.load(tempfilename) == b'xxyyaa'


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
