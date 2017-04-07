# Copyright (c) 2017, Almar Klein
# This file is freely distributed under the terms of the 2-clause BSD License.

"""
The encoder and decoder for the Binary Structured Data Format (BSDF).
"""

# todo: versioning
# todo: binary data
# todo: references
# todo: replacements / extension
# todo: efficient updating -> get access to pos in file
# todo: streaming blob
# todo: schema validation

import sys
import struct

spack = struct.pack
strunpack = struct.unpack


def lencode(x):
    if x < 255:
        return spack('>B', x)
    else:
        return spack('>BQ', 255, x)


def make_encoder():
    
    # From six.py
    if sys.version_info[0] >= 3:
        string_types = str
        integer_types = int
        small_types = type(None), bool, int, float, str
        _intstr = int.__str__
    else:
        string_types = basestring  # noqa
        integer_types = (int, long)  # noqa
        small_types = type(None), bool, int, long, float, basestring
        _intstr = lambda i: str(i).rstrip('L')
    
    _floatstr = float.__repr__
    spack = struct.pack
    # lencode = lambda x: spack('>BQ', 255, x)

    
    def encode_object(write, value):
        
        if value is None:
            write(b'N')
        elif value is True:
            write(b'y')
        elif value is False:
            write(b'n')
        elif isinstance(value, integer_types):
            if 0 <= value <= 255:
                write(b'B' + spack('>B', value))
            #elif -2147483647 <= value <= 2147483647:
            #    return b'i' + spack('>i', value)
            else:
                write(b'q' + spack('>q', value))
        elif isinstance(value, float):
            write(b'd' + spack('>d', value))
        elif isinstance(value, string_types):
            bb = value.encode('utf-8')
            write(b's' + lencode(len(bb)))
            write(bb)
        
        # elif isinstance(value, dict):
        #     encode_dict(write, value)
        # elif isinstance(value, (list, tuple)):
        #     encode_list(write, value)
        
        elif isinstance(value, dict):
            write(b'D' + lencode(len(value)))
            for key, v in value.items():
                assert key.isidentifier()
                #yield ' ' * indent + key
                name_b = key.encode()
                write(lencode(len(name_b)))
                write(name_b)
                encode_object(write, v)
        elif isinstance(value, (list, tuple)):
            write(b'L' + lencode(len(value)))
            for v in value:
                encode_object(write, v)
    
        else:
            # We do not know            
            data = 'Null'
            tmp = repr(value)
            if len(tmp) > 64:
                tmp = tmp[:64] + '...'
            if name is not None:
                print("BSDF: %s is unknown object: %s" %  (name, tmp))
            else:
                print("BSDF: unknown object: %s" % tmp)
    
   
    return encode_object



encode = make_encoder()

from io import BytesIO

def saves(d):
    f = BytesIO()
    # f.write(b'BSDF')
    # f.write(struct.pack('<B', 2))
    # f.write(struct.pack('<B', 0))
    
    encode(f.write, d)
    return f.getvalue()
    #return b''.join(encode(d))
    #f = BytesIO()
    #encode(d, f)
    #return f.getvalue()


dumps = saves  # json compat



## Decoder




def decode_object(f):

    # Get value
    c = f.read(1)
    if c == b'N':
        return None
    elif c == b'y':
        return True
    elif c == b'n':
        return False
    elif c == b'B':
        return strunpack('>B', f.read(1))[0]
    elif c == b'i':
        return strunpack('>i', f.read(4))[0]
    elif c == b'q':
        return strunpack('>q', f.read(8))[0]
    elif c == b'd':
        return strunpack('>d', f.read(8))[0]
    elif c == b's':
        n_s = strunpack('>B', f.read(1))[0]
        if n_s == 255:
            n_s = strunpack('>Q', f.read(8))[0]
        return f.read(n_s).decode()
    
    # elif c == b'D':
    #     yield name, dict(decode_dict(f))
    # elif c == b'L':
    #     yield name, list(decode_list(f))
    
    elif c == b'D':
        value = dict()
        n = strunpack('>B', f.read(1))[0]
        if n == 255:
            n = strunpack('>Q', f.read(8))[0]
        for i in range(n):
            n_name = strunpack('>B', f.read(1))[0]
            if n_name == 255:
                n_name = strunpack('>Q', f.read(8))[0]
            assert n_name > 0
            name = f.read(n_name).decode()
            value[name] = decode_object(f)
        return value
    elif c == b'L':
        n = strunpack('>B', f.read(1))[0]
        if n == 255:
            n = strunpack('>Q', f.read(8))[0]
        return [decode_object(f) for i in range(n)]
    
    else:
        raise RuntimeError('Parse error')


def loads(bb):
    f = BytesIO(bb)
    #assert f.read(1) == b'D'
    #return dict(decode_dict(f))
    return decode_object(f)
    
    #d, bb = decode_dict(bb[1:])
    #assert not bb
    #return d
