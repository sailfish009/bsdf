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
