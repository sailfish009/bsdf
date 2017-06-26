# Copyright (c) 2017, Almar Klein
# This file is freely distributed under the terms of the 2-clause BSD License.

"""
The encoder and decoder for the Binary Structured Data Format (BSDF).
"""

# todo: binary data
# todo: references
# todo: replacements / extension
# todo: efficient updating -> get access to pos in file
# todo: streaming blob
# todo: schema validation

import sys
import struct
import zlib
import bz2
import hashlib

spack = struct.pack
strunpack = struct.unpack


# Versioning. The version_info applies to the implementation. The major
# and minor numbers are equal to the file format itself. The major
# number if increased when backward incompatible changes are introduced.
# An implementation must raise an exception when the file being read
# has a higher major version. The minor number when new backward
# compatible features are introduced. An implementation must display a
# warning when the file being read has a higher minor version. The patch
# version is increased for fixes and improving of the implementation.
version_info = 2, 0, 0
format_version = version_info[:2]
__version__ = '.'.join(str(i) for i in version_info)



def lencode(x):
    if x < 255:
        return spack('<B', x)
    else:
        return spack('<BQ', 255, x)

SIZE_INF = 2**56


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
    # spack = struct.pack
    # lencode = lambda x: spack('<B', x) if x < 255 else spack('<BQ', 255, x)
    
    def encode_object(ctx, value, stream_ob, converter_id=None):
        
        if converter_id is not None:
            # ctx.converter_use[converter_id] = True
            bb = converter_id.encode('utf-8')  # todo: assert that's smaller than 256 bytes
            converter_patch = lencode(len(bb)) + bb
            x = lambda i: i.upper() + converter_patch
        else:
            x = lambda i: i
        
        if value is None:
            ctx.write(x(b'v'))  # V for void
        elif value is True:
            ctx.write(x(b'y'))  # Y for yes
        elif value is False:
            ctx.write(x(b'n'))  # N for no
        elif isinstance(value, integer_types):
            if 0 <= value <= 255:
                ctx.write(x(b'u') + spack('B', value))  # U for uint8
            else:
                ctx.write(x(b'i') + spack('<q', value))  # I for int
        elif isinstance(value, float):
            ctx.write(x(b'd') + spack('<d', value))  # D for double
            # todo: allow 32bit float via arg
        elif isinstance(value, string_types):
            bb = value.encode('utf-8')
            ctx.write(x(b's') + lencode(len(bb)))  # S for str
            ctx.write(bb)
        elif isinstance(value, (list, tuple)):
            ctx.write(x(b'l') + lencode(len(value)))  # L for list
            for v in value:
                encode_object(ctx, v, stream_ob)
        elif isinstance(value, dict):
            ctx.write(x(b'm') + lencode(len(value)))  # M for mapping
            for key, v in value.items():
                assert key.isidentifier()
                #yield ' ' * indent + key
                name_b = key.encode()
                ctx.write(lencode(len(name_b)))
                ctx.write(name_b)
                encode_object(ctx, v, stream_ob)
        elif isinstance(value, bytes):
            # todo: many things to decide for binary
            # - what compression to support?
            # - do we include a hash? of raw or compressed data?
            # - dp we also byte-align for compressed data?
            if ctx.compression == b'\x00':
                bb = value
            elif ctx.compression == b'x01':
                bb = zlib.compress(value)
            elif ctx.compression == b'\x01':
                bb = bz2.compress(value)
            else:
                assert False, 'Unknown compression identifier'
            ctx.write(b'b')  # B for blob
            ctx.write(spack('B', ctx.compression))
            ctx.write(lencode(len(bb)))
            ctx.write(lencode(len(value)))
            if ctx.makehash:
                ctx.write(b'\xff' + hashlib.md5(value).digest())
            else:
                ctx.write(b'\x00')
            i = ctx.tell() + 1
            ctx.write(spack('<B'. i % 8))  # padding for byte alignment
            ctx.write(bb)
        elif isinstance(value, BaseStream):
            # Initialize the stream
            if isinstance(value, ListStream):
                ctx.write(x(b'l') + lencode(SIZE_INF))  # L for list
            else:
                assert False, 'only ListStream is supported'
            # Mark this as *the* stream, and activate the stream.
            # The save() function verifies this is the last written object.
            if ctx.stream is not None:
                raise RuntimeError('Can only have one stream per file.')
            ctx.stream = value
            value._activate(ctx)
        else:
            # Try if the value is of a type we know
            x = ctx.converters_index.get(value.__class__, None)
            # Maybe its a subclass of a type we know
            if x is None:
                for cls, x in ctx.converters_index.items():
                    if isinstance(value, cls):
                        break
                else:
                    x = None
            # Success or fail
            if x is not None:
                converter_id2, converter_func = x
                if converter_id == converter_id2:
                    raise RuntimeError('Circular recursion in converter funcs!')
                encode_object(ctx, converter_func(ctx, value), stream_ob, converter_id2)
            else:
                t = ('Class %r is not a valid base BSDF type, nor is it '
                     'handled by a converter.')
                raise TypeError(t % value.__class__.__name__)
    
    return encode_object

   

encode = make_encoder()

from io import BytesIO

def saves(ob, converters=None, compression=0):
    f = BytesIO()
    save(f, ob, converters, compression)
    return f.getvalue()


def save(f, ob, converters=None, compression=0, stream=None):
    f.write(b'BSDF')
    f.write(struct.pack('<B', format_version[0]))
    f.write(struct.pack('<B', format_version[1]))
    
    # Prepare converters
    f.converters = converters or {}
    f.converters_index = {}
    for key in f.converters:
        cls, func = f.converters[key]
        f.converters_index[cls] = key, func
    
    # Prepare streaming
    f.stream = None
    
    # prepare compression
    f.compression = compression
    
    last_value = encode(f, ob, stream)
    
    # Verify that stream object was at the end, and add initial elements
    if f.stream is not None:
        if f.stream.start_pos != f.tell():
            raise ValueError('The stream object must be the last object to be encoded.')


class BaseStream(object):
    pass


class ListStream(BaseStream):
    
    def __init__(self):
        self.f = None
        self.start_pos = 0
        self.count = 0
    
    def _activate(self, file):
        if self.f is not None:  # This could happen if present twice in the ob
            raise RuntimeError('Stream object cnanot be activated twice?')
        self.f = file
        self.start_pos = self.f.tell()
    
    def append(self, item):
        if self.f is None:
            raise RuntimeError('List streamer is not ready for streaming yet.')
        encode(self.f, item, None)
        self.count += 1
    
    def close(self):
        if self.f is None:
            raise RuntimeError('List streamer is not opened yet.')
        i = self.f.tell()
        self.f.seek(self.start_pos - 8)
        self.f.write(spack('<Q', self.count))
        self.f.seek(i)


dumps = saves  # json compat

def make_encoder2():
    return saves



## Decoder




def decode_object(ctx):

    # Get value
    char = ctx.read(1)
    c = char.lower()
    
    # Conversion (uppercase value identifiers signify converted values)
    if not char:
        raise EOFError()
    elif char != c:
        n = strunpack('<B', ctx.read(1))[0]
        if n == 255: n = strunpack('<Q', ctx.read(8))[0]
        converter_id = ctx.read(n).decode('utf-8')
    else:
        converter_id = None
    
    if c == b'v':
        value = None
    elif c == b'y':
        value = True
    elif c == b'n':
        value = False
    elif c == b'u':
        value = strunpack('<B', ctx.read(1))[0]
    elif c == b'i':
        value = strunpack('<q', ctx.read(8))[0]
    elif c == b'f':
        value = strunpack('<f', ctx.read(4))[0]
    elif c == b'd':
        value = strunpack('<d', ctx.read(8))[0]
    elif c == b's':
        n_s = strunpack('<B', ctx.read(1))[0]
        if n_s == 255: n_s = strunpack('<Q', ctx.read(8))[0]
        value = ctx.read(n_s).decode('utf-8')  # todo: can we do more efficient utf-8?
    elif c == b'l':
        n = strunpack('<B', ctx.read(1))[0]
        if n == 255: n = strunpack('<Q', ctx.read(8))[0]
        if n == SIZE_INF:
            value = []
            try:
                while True:
                    value.append(decode_object(ctx))
            except EOFError:
                pass
        else:
            value = [decode_object(ctx) for i in range(n)]
    elif c == b'm':
        value = dict()
        n = strunpack('<B', ctx.read(1))[0]
        if n == 255: n = strunpack('<Q', ctx.read(8))[0]
        for i in range(n):
            n_name = strunpack('<B', ctx.read(1))[0]
            if n_name == 255: n_name = strunpack('<Q', ctx.read(8))[0]
            assert n_name > 0
            name = ctx.read(n_name).decode()
            value[name] = decode_object(ctx)
    else:
        raise RuntimeError('Parse error')
    
    # Convert value if we have a converter for it
    if converter_id is not None:
        converter = ctx.converters.get(converter_id, None)
        if converter is not None:
            value = converter(ctx, value)
        else:
            print('no converter found for %r' % converter_id)
    
    return value


def loads(bb, converters=None):
    
    f = BytesIO(bb)
    
    f.converters = converters or {}
    
    # Check magic string
    if f.read(4) != b'BSDF':
        raise RuntimeError('This does not look a BSDF file.')
    
    # Check version
    major_version = strunpack('<B', f.read(1))[0]
    minor_version = strunpack('<B', f.read(1))[0]
    file_version = '%i.%i' % (major_version, minor_version)
    if major_version != format_version[0]:  # major version should be 2
        t = 'Warning: reading file with higher major version (%s) than the implemntation (%s).'
        raise RuntimeError(t % (__version__, file_version))
    if minor_version > format_version[1]:  # minor version should be smaller than ours
        t = 'Warning: reading file with higher minor version (%s) than the implemntation (%s).'
        print(t % (__version__, file_version))
    
    return decode_object(f)


def make_decoder2():
    return loads
