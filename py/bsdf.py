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
    
    def encode_dict(val, indent=None):
        
        for key, value in val.items():
            assert key.isidentifier()
            #yield ' ' * indent + key
            name_b = key.encode()
            yield lencode(len(name_b))
            yield name_b
            yield encode_object(value)
            #for x in encode_object(value):
            #    yield x
    
    def encode_list(val):
        
        for value in val:
            yield encode_object(value)
            #for x in encode_object(value):
            #    yield x
    
    def encode_object(value):
        
        if value is None:
            return b'N'
        elif value is True:
            return b'y'
        elif value is False:
                return b'n'
        elif isinstance(value, integer_types):
            if 0 <= value <= 255:
                return b'B' + spack('>B', value)
            #elif -2147483647 <= value <= 2147483647:
            #    return b'i' + spack('>i', value)
            else:
                return b'q' + spack('>q', value)
        elif isinstance(value, float):
            return b'd' + spack('>d', value)
        elif isinstance(value, string_types):
            bb = value.encode()
            return b's' + lencode(len(bb)) + bb
        elif isinstance(value, dict):
            return b'D' + lencode(len(value)) + b''.join(encode_dict(value))
            #for x in encode_dict(value):
            #    yield x
        elif isinstance(value, (list, tuple)):
            return b'L' + lencode(len(value)) + b''.join(encode_list(value))
            #for x in encode_list(value):
            #    yield x
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
    return encode(d)
    #return b''.join(encode(d))
    #f = BytesIO()
    #encode(d, f)
    #return f.getvalue()


dumps = saves  # json compat



## Decoder



# def lendecode(bb):
#     n = strunpack('>B', bb[:1])[0]
#     if n < 255:
#         return n, bb[1:]
#     else:
#         return strunpack('>Q', bb[1:9])[0], bb[9:]


# def decode_dict(bb):
#     n, bb = lendecode(bb)
#     value = {}
#     for i in range(n):
#         # Get name
#         n_name, bb = lendecode(bb)
#         assert n_name > 0
#         name = bb[:n_name].decode()
#         # Get value
#         c = bb[n_name:n_name+1]
#         bb = bb[n_name+1:]
#         if c == b'N':
#             value[name] = None
#         elif c == b'y':
#             value[name] = True
#         elif c == b'n':
#             value[name] = False
#         elif c == b'B':
#             value[name] = strunpack('>B', bb[:1])[0]
#             bb = bb[1:]
#         elif c == b'i':
#             value[name] = strunpack('>i', bb[:4])[0]
#             bb = bb[4:]
#         elif c == b'q':
#             value[name] = strunpack('>q', bb[:8])[0]
#             bb = bb[8:]
#         elif c == b'd':
#             value[name] = strunpack('>d', bb[:8])[0]
#             bb = bb[8:]
#         elif c == b's':
#             n_s, bb = lendecode(bb)
#             value[name] = bb[:n_s].decode()
#             bb = bb[n_s:]
#         elif c == b'D':
#             value[name], bb = decode_dict(bb)
#         elif c == b'L':
#             raise NotImplementedError()
#         else:
#             raise RuntimeError('Parse error')
#     
#     return value, bb


def decode_dict(f):
    n = strunpack('>B', f.read(1))[0]
    if n == 255:
        n = strunpack('>Q', f.read(8))[0]
    
    for i in range(n):
        # Get name
        n_name = strunpack('>B', f.read(1))[0]
        if n_name == 255:
            n_name = strunpack('>Q', f.read(8))[0]
        assert n_name > 0
        name = f.read(n_name).decode()
        # Get value
        c = f.read(1)
        if c == b'N':
            yield name, None
        elif c == b'y':
            yield name, True
        elif c == b'n':
            yield name, False
        elif c == b'B':
            yield name, strunpack('>B', f.read(1))[0]
        elif c == b'i':
            yield name, strunpack('>i', f.read(4))[0]
        elif c == b'q':
            yield name, strunpack('>q', f.read(8))[0]
        elif c == b'd':
            yield name, strunpack('>d', f.read(8))[0]
        elif c == b's':
            n_s = strunpack('>B', f.read(1))[0]
            if n_s == 255:
                n_s = strunpack('>Q', f.read(8))[0]
            yield name, f.read(n_s).decode()
        elif c == b'D':
            yield name, dict(decode_dict(f))
        elif c == b'L':
            yield name, list(decode_list(f))
        else:
            raise RuntimeError('Parse error')


def decode_list(f):
    n = strunpack('>B', f.read(1))[0]
    if n == 255:
        n = strunpack('>Q', f.read(8))[0]
    
    for i in range(n):
        # Get value
        c = f.read(1)
        if c == b'N':
            yield None
        elif c == b'y':
            yield True
        elif c == b'n':
            yield False
        elif c == b'B':
            yield strunpack('>B', f.read(1))[0]
        elif c == b'i':
            yield strunpack('>i', f.read(4))[0]
        elif c == b'q':
            yield strunpack('>q', f.read(8))[0]
        elif c == b'd':
            yield strunpack('>d', f.read(8))[0]
        elif c == b's':
            n_s = strunpack('>B', f.read(1))[0]
            if n_s == 255:
                n_s = strunpack('>Q', f.read(8))[0]
            yield f.read(n_s).decode()
        elif c == b'D':
            yield dict(decode_dict(f))
        elif c == b'L':
            yield list(decode_list(f))
        else:
            raise RuntimeError('Parse error')


def loads(bb):
    f = BytesIO(bb)
    assert f.read(1) == b'D'
    return dict(decode_dict(f))
    
    #d, bb = decode_dict(bb[1:])
    #assert not bb
    #return d
