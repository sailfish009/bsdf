# Copyright (c) 2017, Almar Klein
# This file is freely distributed under the terms of the 2-clause BSD License.

"""
Python implementation of the Binary Structured Data Format (BSDF).

BSDF is a binary format for serializing structured (scientific) data.
Read more at https://gitlab.com/almarklein/bsdf.

This implementation is relatively sophisticated; a simple BSDF serializer
without support for streaming and lazy blob loading could be much more compact.

This module has no dependencies and works on Python 2.7 and 3.4+.

Note: on Legacy Python (Python 2.7), non-Unicode strings are encoded as bytes.
"""

# todo: in 2020, remove six stuff, __future__ and _isidentifier
# todo: in 2020, remove 'utf-8' args to encode/decode; it's faster
# todo: blob resizing
# todo: schema validation

from __future__ import absolute_import, division, print_function

import bz2
import hashlib
import logging
import re
import struct
import sys
import types
import zlib
from io import BytesIO

logger = logging.getLogger(__name__)

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


# %% The encoder and decoder implementation

# From six.py
PY3 = sys.version_info[0] >= 3
if PY3:
    string_types = str
    unicode_types = str
    integer_types = int
    classtypes = type
else:  # pragma: no cover
    string_types = basestring  # noqa
    unicode_types = unicode  # noqa
    integer_types = (int, long)  # noqa
    classtypes = type, types.ClassType

# Shorthands
spack = struct.pack
strunpack = struct.unpack


def lencode(x):
    """ Encode an unsigned integer into a variable sized blob of bytes.
    """
    # We could support 16 bit and 32 bit as well, but the gain is low, since
    # 9 bytes for collections with over 250 elements is marginal anyway.
    if x <= 250:
        return spack('<B', x)
    # elif x < 65536:
    #     return spack('<BH', 251, x)
    # elif x < 4294967296:
    #     return spack('<BI', 252, x)
    else:
        return spack('<BQ', 253, x)


# Include len decoder for completeness; we've inlined it for performance.
def lendecode(f):
    """ Decode an unsigned integer from a file.
    """
    n = strunpack('<B', f.read(1))[0]
    if n == 253: n = strunpack('<Q', f.read(8))[0]  # noqa
    return n


def encode_type_id(b, extension_id):
    """ Encode the type identifier, with or without extension id.
    """
    if extension_id is not None:
        bb = extension_id.encode('UTF-8')
        return b.upper() + lencode(len(bb)) + bb  # noqa
    else:
        return b  # noqa


def _isidentifier(s):
    """ Use of str.isidentifier() for Legacy Python, but slower.
    """
    # http://stackoverflow.com/questions/2544972/
    return (isinstance(s, str) and
            re.match(r'^\w+$', s, re.UNICODE) and
            re.match(r'^[0-9]', s) is None)


class BsdfSerializer(object):
    """ Instances of this class represent a BSDF encoder/decoder.

    It acts as a placeholder for a set of extensions and encoding/decoding
    options. Use this to predefine extensions and options for high
    performance encoding/decoding. For general use, see the functions
    `save()`, `encode()`, `load()`, and `decode()`.

    This implementation of BSDF supports streaming lists (keep adding
    to a list after writing the main file), lazy loading of blobs, and
    in-place editing of blobs (for streams opened with a+).

    Options for encoding:

    * compression (int or str): ``0`` or "no" for no compression (default),
      ``1`` or "zlib" for Zlib compression (same as zip files and PNG), and
      ``2`` or "bz2" for Bz2 compression (more compact but slower writing).
      Note that some BSDF implementations (e.g. JavaScript) may not support
      compression.
    * use_checksum (bool): whether to include a checksum with binary blobs.
    * float64 (bool): Whether to write floats as 64 bit (default) or 32 bit.

    Options for decoding:

    * load_streaming (bool): if True, and the final object in the structure was
      a stream, will make it available as a stream in the decoded object.
    * lazy_blob (bool): if True, bytes are represented as Blob objects that can
      be used to lazily access the data, and also overwrite the data if the
      file is open in a+ mode.
    """

    def __init__(self, extensions=None, **options):
        self._extensions = {}  # name -> extension
        self._extensions_by_cls = {}  # cls -> (name, extension.encode)
        if extensions is None:
            extensions = standard_extensions
        for extension in extensions:
            self.add_extension(extension)
        self._parse_options(**options)

    def _parse_options(self,
                       compression=0, use_checksum=False, float64=True,
                       load_streaming=False, lazy_blob=False):

        # Validate compression
        if isinstance(compression, string_types):
            m = {'no': 0, 'zlib': 1, 'bz2': 2}
            compression = m.get(compression.lower(), compression)
        if compression not in (0, 1, 2):
            raise TypeError('Compression must be 0, 1, 2, '
                            '"no", "zlib", or "bz2"')
        self._compression = compression

        # Other encoding args
        self._use_checksum = bool(use_checksum)
        self._float64 = bool(float64)

        # Decoding args
        self._load_streaming = bool(load_streaming)
        self._lazy_blob = bool(lazy_blob)

    def add_extension(self, extension_class):
        """ Add an extension to this serializer instance, which must be
        a subclass of Extension.
        """
        # Check class
        if not (isinstance(extension_class, type) and
                issubclass(extension_class, Extension)):
            raise TypeError('add_extension() expects a Extension class.')
        extension = extension_class()

        # Get name
        name = extension.name
        if not isinstance(name, str):
            raise TypeError('Extension name must be str.')
        if len(name) == 0 or len(name) > 250:
            raise NameError('Extension names must be nonempty and shorter '
                            'than 251 chars.')
        if name in self._extensions:
            logger.warn('Overwriting extension "%s", '
                        'consider removing first' % name)

        # Get classes
        cls = extension.cls
        if not cls:
            clss = []
        elif isinstance(cls, (tuple, list)):
            clss = cls
        else:
            clss = [cls]
        for cls in clss:
            if not isinstance(cls, classtypes):
                raise TypeError('Extension classes must be types.')

        # Store
        for cls in clss:
            self._extensions_by_cls[cls] = name, extension.encode
        self._extensions[name] = extension

    def remove_extension(self, name):
        """ Remove a converted by its unique name.
        """
        if not isinstance(name, str):
            raise TypeError('Extension name must be str.')
        if name in self._extensions:
            self._extensions.pop(name)
        for cls in list(self._extensions_by_cls.keys()):
            if self._extensions_by_cls[cls][0] == name:
                self._extensions_by_cls.pop(cls)

    def _encode(self, f, value, streams, extension_id):
        """ Main encoder function.
        """
        x = encode_type_id
        
        if value is None:
            f.write(x(b'v', extension_id))  # V for void
        elif value is True:
            f.write(x(b'y', extension_id))  # Y for yes
        elif value is False:
            f.write(x(b'n', extension_id))  # N for no
        elif isinstance(value, integer_types):
            if -32768 <= value <= 32767:
                f.write(x(b'h', extension_id) + spack('h', value))  # H for ...
            else:
                f.write(x(b'i', extension_id) + spack('<q', value))  # I for int
        elif isinstance(value, float):
            if self._float64:
                f.write(x(b'd', extension_id) + spack('<d', value))  # D for double
            else:
                f.write(x(b'f', extension_id) + spack('<f', value))  # f for float
        elif isinstance(value, unicode_types):
            bb = value.encode('UTF-8')
            f.write(x(b's', extension_id) + lencode(len(bb)))  # S for str
            f.write(bb)
        elif isinstance(value, (list, tuple)):
            f.write(x(b'l', extension_id) + lencode(len(value)))  # L for list
            for v in value:
                self._encode(f, v, streams, None)
        elif isinstance(value, dict):
            f.write(x(b'm', extension_id) + lencode(len(value)))  # M for mapping
            for key, v in value.items():
                if PY3:
                    assert key.isidentifier()  # faster
                else:
                    assert _isidentifier(key)
                # yield ' ' * indent + key
                name_b = key.encode('UTF-8')
                f.write(lencode(len(name_b)))
                f.write(name_b)
                self._encode(f, v, streams, None)
        elif isinstance(value, bytes):
            f.write(x(b'b', extension_id))  # B for blob
            blob = Blob(value, compression=self._compression,
                        use_checksum=self._use_checksum)
            blob._to_file(f)  # noqa
        elif isinstance(value, Blob):
            f.write(x(b'b', extension_id))  # B for blob
            value._to_file(f)  # noqa
        elif isinstance(value, BaseStream):
            # Initialize the stream
            if isinstance(value, ListStream):
                f.write(x(b'l', extension_id) + spack('<BQ', 255, 0))  # L for list
            else:
                raise TypeError('Only ListStream is supported')
            # Mark this as *the* stream, and activate the stream.
            # The save() function verifies this is the last written object.
            if len(streams) > 0:
                raise ValueError('Can only have one stream per file.')
            streams.append(value)
            value._activate(f, self._encode, self._decode)  # noqa
        else:
            # Try if the value is of a type we know
            x = self._extensions_by_cls.get(value.__class__, None)
            # Maybe its a subclass of a type we know
            if x is None:
                for name, c in self._extensions.items():
                    if c.match(self, value):
                        x = name, c.encode
                        break
                else:
                    x = None
            # Success or fail
            if x is not None:
                extension_id2, extension_encode = x
                if extension_id == extension_id2:
                    raise ValueError('Circular recursion in extension func!')
                self._encode(f, extension_encode(self, value),
                             streams, extension_id2)
            else:
                t = ('Class %r is not a valid base BSDF type, nor is it '
                     'handled by an extension.')
                raise TypeError(t % value.__class__.__name__)

    def _decode(self, f):
        """ Main decoder function.
        """

        # Get value
        char = f.read(1)
        c = char.lower()

        # Conversion (uppercase value identifiers signify converted values)
        if not char:
            raise EOFError()
        elif char != c:
            n = strunpack('<B', f.read(1))[0]
            # if n == 253: n = strunpack('<Q', f.read(8))[0]  # noqa - noneed
            extension_id = f.read(n).decode('UTF-8')
        else:
            extension_id = None

        if c == b'v':
            value = None
        elif c == b'y':
            value = True
        elif c == b'n':
            value = False
        elif c == b'h':
            value = strunpack('<h', f.read(2))[0]
        elif c == b'i':
            value = strunpack('<q', f.read(8))[0]
        elif c == b'f':
            value = strunpack('<f', f.read(4))[0]
        elif c == b'd':
            value = strunpack('<d', f.read(8))[0]
        elif c == b's':
            n_s = strunpack('<B', f.read(1))[0]
            if n_s == 253: n_s = strunpack('<Q', f.read(8))[0]  # noqa
            value = f.read(n_s).decode('UTF-8')
        elif c == b'l':
            n = strunpack('<B', f.read(1))[0]
            if n == 255:
                # Streaming
                n = strunpack('<Q', f.read(8))[0]  # zero if not closed
                # todo: if n > 0, we don't have to do the while loop
                if self._load_streaming:
                    value = ListStream()
                    value._activate(f, self._encode, self._decode)  # noqa
                else:
                    value = []
                    try:
                        while True:
                            value.append(self._decode(f))
                    except EOFError:
                        pass
            else:
                # Normal
                if n == 253: n = strunpack('<Q', f.read(8))[0]  # noqa
                value = [self._decode(f) for i in range(n)]
        elif c == b'm':
            value = dict()
            n = strunpack('<B', f.read(1))[0]
            if n == 253: n = strunpack('<Q', f.read(8))[0]  # noqa
            for i in range(n):
                n_name = strunpack('<B', f.read(1))[0]
                if n_name == 253: n_name = strunpack('<Q', f.read(8))[0]  # noqa
                assert n_name > 0
                name = f.read(n_name).decode('UTF-8')
                value[name] = self._decode(f)
        elif c == b'b':
            if self._lazy_blob:
                value = Blob((f, True))
            else:
                blob = Blob((f, False))
                value = blob.get_bytes()
        else:
            raise RuntimeError('Parse error %r' % char)

        # Convert value if we have an extension for it
        if extension_id is not None:
            extension = self._extensions.get(extension_id, None)
            if extension is not None:
                value = extension.decode(self, value)
            else:
                # todo: warn/log instead of print
                print('no extension found for %r' % extension_id)

        return value

    def encode(self, ob):
        """ Save the given object to bytes.
        """
        f = BytesIO()
        self.save(f, ob)
        return f.getvalue()

    def save(self, f, ob):
        """ Write the given object to the given file object.
        """
        f.write(b'BSDF')
        f.write(struct.pack('<B', format_version[0]))
        f.write(struct.pack('<B', format_version[1]))

        # Prepare streaming, this list will have 0 or 1 item at the end
        streams = []

        self._encode(f, ob, streams, None)

        # Verify that stream object was at the end, and add initial elements
        if len(streams) > 0:
            stream = streams[0]
            if stream.start_pos != f.tell():
                raise ValueError('The stream object must be '
                                 'the last object to be encoded.')

    def decode(self, bb):
        """ Load the data structure that is BSDF-encoded in the given bytes.
        """
        f = BytesIO(bb)
        return self.load(f)

    def load(self, f):
        """ Load a BSDF-encoded object from the given file object.
        """
        # Check magic string
        f4 = f.read(4)
        if f4 != b'BSDF':
            raise RuntimeError('This does not look like a BSDF file: %r' % f4)
        # Check version
        major_version = strunpack('<B', f.read(1))[0]
        minor_version = strunpack('<B', f.read(1))[0]
        file_version = '%i.%i' % (major_version, minor_version)
        if major_version != format_version[0]:  # major version should be 2
            t = ('Reading file with different major version (%s) '
                 'from the implementation (%s).')
            raise RuntimeError(t % (__version__, file_version))
        if minor_version > format_version[1]:  # minor should be < ours
            # todo: warn/log instead of print
            t = ('Warning: reading file with higher minor version (%s) '
                 'than the implementation (%s).')
            print(t % (__version__, file_version))

        return self._decode(f)


# %% Streaming and blob-files


class BaseStream(object):
    """ Base class for streams.
    """
    pass


class ListStream(BaseStream):
    """ A streamable list object used for writing or reading.
    """

    def __init__(self):
        self.f = None
        self.start_pos = 0
        self.count = 0

    def _activate(self, file, encode_func, decode_func):
        if self.f is not None:  # This could happen if present twice in the ob
            raise RuntimeError('Stream object cnanot be activated twice?')
        self.f = file
        self.start_pos = self.f.tell()
        self._encode = encode_func
        self._decode = decode_func

    def append(self, item):
        """ Append an item to the list.
        """
        if self.f is None:
            raise RuntimeError('List streamer is not ready for streaming yet.')
        # todo: this was encode, is save() correct?
        self._encode(self.f, item, [self], None)
        self.count += 1

    def close(self):
        """ Close the stream, writing the size.
        """
        # todo: prevent breaking things when used for reading!
        if self.f is None:
            raise RuntimeError('List streamer is not opened yet.')
        i = self.f.tell()
        self.f.seek(self.start_pos - 8)
        self.f.write(spack('<Q', self.count))
        # todo: set first size byte to 254 to indicate a closed stream?
        self.f.seek(i)

    def get_next(self):
        """ Get the next element in the stream.
        """
        # todo: prevent mixing write/read ops, or is that handy in a+?
        # This raises EOFError at some point.
        try:
            return self._decode(self.f)
        except EOFError:
            raise StopIteration()

        # todo: allow iterating over the stream


class Blob(object):
    """ Object to represent a blob of bytes. When used to write a BSDF file,
    it's a wrapper for bytes plus properties such as what compression to apply.
    When used to read a BSDF file, it can be used to read the data lazily, and
    also modify the data if reading in 'a+' mode and the blob isn't compressed.
    """

    # For now, this does not allow re-sizing blobs (within the allocated size)
    # but this can be added later.

    def __init__(self, f, compression=0, extra_size=0, use_checksum=False):
        if isinstance(f, bytes):
            self.f = None
            self.compressed = self._from_bytes(f, compression)
            self.compression = compression
            self.allocated_size = self.used_size + extra_size
            self.use_checksum = use_checksum
        elif isinstance(f, tuple) and len(f) == 2 and hasattr(f[0], 'read'):
            self.f, allow_seek = f
            self.compressed = None
            self._from_file(self.f, allow_seek)
            self._modified = False
        else:
            raise RuntimeError('Wrong argument to create Blob.')

    def _from_bytes(self, value, compression):
        """ When used to wrap bytes in a blob.
        """
        if compression == 0:
            compressed = value
        elif compression == 1:
            compressed = zlib.compress(value)
        elif compression == 2:
            compressed = bz2.compress(value)
        else:
            assert False, 'Unknown compression identifier'

        self.data_size = len(value)
        self.used_size = len(compressed)
        return compressed

    def _to_file(self, f):
        """ Private friend method called by encoder to write a blob to a file.
        """
        # Write sizes - write at least in a size that allows resizing
        if self.allocated_size <= 250 and self.compression == 0:
            f.write(spack('<B', self.allocated_size))
            f.write(spack('<B', self.used_size))
            f.write(lencode(self.data_size))
        else:
            f.write(spack('<BQ', 253, self.allocated_size))
            f.write(spack('<BQ', 253, self.used_size))
            f.write(spack('<BQ', 253, self.data_size))
        # Compression and checksum
        f.write(spack('B', self.compression))
        if self.use_checksum:
            f.write(b'\xff' + hashlib.md5(self.compressed).digest())
        else:
            f.write(b'\x00')
        # Byte alignment (only necessary for uncompressed data)
        if self.compression == 0:
            alignment = 8 - (f.tell() + 1) % 8  # +1 for the byte to write
            f.write(spack('<B', alignment))  # padding for byte alignment
            f.write(b'\x00' * alignment)
        else:
            f.write(spack('<B', 0))
        # The actual data and extra space
        f.write(self.compressed)
        f.write(b'\x00' * (self.allocated_size - self.used_size))

    def _from_file(self, f, allow_seek):
        """ Used when a blob is read by the decoder.
        """
        # Read blob header data (5 to 42 bytes)
        # Size
        allocated_size = strunpack('<B', f.read(1))[0]
        if allocated_size == 253: allocated_size = strunpack('<Q', f.read(8))[0]  # noqa
        used_size = strunpack('<B', f.read(1))[0]
        if used_size == 253: used_size = strunpack('<Q', f.read(8))[0]  # noqa
        data_size = strunpack('<B', f.read(1))[0]
        if data_size == 253: data_size = strunpack('<Q', f.read(8))[0]  # noqa
        # Compression and checksum
        compression = strunpack('<B', f.read(1))[0]
        has_checksum = strunpack('<B', f.read(1))[0]
        if has_checksum:
            checksum = f.read(16)
        # Skip alignment
        alignment = strunpack('<B', f.read(1))[0]
        f.read(alignment)
        # Get or skip data + extra space
        if allow_seek:
            self.start_pos = f.tell()
            self.end_pos = self.start_pos + used_size
            f.seek(self.start_pos + allocated_size)
        else:
            self.start_pos = None
            self.end_pos = None
            self.compressed = f.read(used_size)
            f.read(allocated_size - used_size)
        # Store info
        self.alignment = alignment
        self.compression = compression
        self.use_checksum = checksum if has_checksum else None
        self.used_size = used_size
        self.allocated_size = allocated_size
        self.data_size = data_size

    def seek(self, p):
        """ Seek to the given position (relative to the blob start).
        """
        if self.f is None:
            raise RuntimeError('Cannot seek in a blob '
                               'that is not created by the BSDF decoder.')
        if p < 0:
            p = self.end_pos - p
        if p < 0 or p > self.used_size:
            raise IndexError('Seek beyond blob boundaries.')
        self.f.seek(self.start_pos + p)

    def tell(self):
        """ Get the current file pointer position (relative to the blob start).
        """
        if self.f is None:
            raise RuntimeError('Cannot tell in a blob '
                               'that is not created by the BSDF decoder.')
        self.f.tell() - self.start_pos

    def write(self, bb):
        """ Write bytes to the blob.
        """
        if self.f is None:
            raise RuntimeError('Cannot write in a blob '
                               'that is not created by the BSDF decoder.')
        if self.compression:
            raise IndexError('Cannot arbitrarily write in compressed blob.')
        if self.f.tell() + len(bb) > self.end_pos:
            raise IndexError('Write beyond blob boundaries.')
        self._modified = True
        return self.f.write(bb)

    def read(self, n):
        """ Read n bytes from the blob.
        """
        if self.f is None:
            raise RuntimeError('Cannot read in a blob '
                               'that is not created by the BSDF decoder.')
        if self.compression:
            raise IndexError('Cannot arbitrarily read in compressed blob.')
        if self.f.tell() + n > self.end_pos:
            raise IndexError('Read beyond blob boundaries.')
        return self.f.read(n)

    def get_bytes(self):
        """ Get the contents of the blob as bytes.
        """
        if self.compressed is not None:
            compressed = self.compressed
        else:
            self.seek(0)
            compressed = self.f.read(self.used_size)
        if self.compression == 0:
            value = compressed
        elif self.compression == 1:
            value = zlib.decompress(compressed)
        elif self.compression == 2:
            value = bz2.decompress(compressed)
        else:
            raise RuntimeError('Invalid compression %i' % self.compression)
        return value

    def close(self):
        """ Reset the checksum if present.
        """
        # or ... should the presence of a checksum mean that data is proteced?
        if self.checksum is not None and self._modified:
            self.seek(0)
            compressed = self.f.read(self.used_size)
            self.f.seek(self.start_pos - self.alignment - 16)
            self.f.write(hashlib.md5(compressed).digest())


# %% High-level functions


def encode(ob, extensions=None, **options):
    """ Save (BSDF-encode) the given object to bytes.
    See `BSDFSerializer` for details on extensions and options.
    """
    s = BsdfSerializer(extensions, **options)
    return s.encode(ob)


# todo: allow f and ob to be reversed
def save(f, ob, extensions=None, **options):
    """ Save (BSDF-encode) the given object to the given filename or
    file object. See` BSDFSerializer` for details on extensions and options.
    """
    s = BsdfSerializer(extensions, **options)
    if isinstance(f, string_types):
        with open(f, 'wb') as fp:
            return s.save(fp, ob)
    else:
        return s.save(f, ob)


def decode(bb, extensions=None, **options):
    """ Load a (BSDF-encoded) structure from bytes.
    See `BSDFSerializer` for details on extensions and options.
    """
    s = BsdfSerializer(extensions, **options)
    return s.decode(bb)


def load(f, extensions=None, **options):
    """ Load a (BSDF-encoded) structure from the given filename or file object.
    See `BSDFSerializer` for details on extensions and options.
    """
    s = BsdfSerializer(extensions, **options)
    if isinstance(f, string_types):
        with open(f, 'rb') as fp:
            return s.load(fp)
    else:
        return s.load(f)


# Aliases for json compat
loads = decode
dumps = encode


# %% Standard extensions

# Defining extensions as a dict would be more compact and feel lighter, but
# that would only allow lambdas, which is too limiting, e.g. for ndarray
# extension.

class Extension(object):
    """ Base class to implement BSDF extensions for special data types.

    Extension classes are provided to the BSDF serializer, which
    instantiates the class. That way, the extension can be somewhat dynamic:
    e.g. the NDArrayExtension exposes the ndarray class only when numpy
    is imported.

    A extension instance must have two attributes. These can be attribiutes of
    the class, or of the instance set in ``__init__()``:

    * name (str): the name by which encoded values will be identified.
    * cls (type): the type (or list of types) to match values with.
      This is optional, but it makes the encoder select extensions faster.

    Further, it needs 3 methods:

    * `match(serializer, value) -> bool`: return whether the extension can
      convert the given value. The default is ``isinstance(value, self.cls)``.
    * `encode(serializer, value) -> encoded_value`: the function to encode a
      value to more basic data types.
    * `decode(serializer, encoded_value) -> value`: the function to decode an
      encoded value back to its intended representation.

    """

    name = ''
    cls = ()

    def __repr__(self):
        return '<BSDF extension %r at 0x%s>' % (self.name, hex(id(self)))

    def match(self, s, v):
        return isinstance(v, self.cls)

    def encode(self, s, v):
        return v

    def decode(self, s, v):
        return v


class ComplexExtension(Extension):

    name = 'c'
    cls = complex

    def encode(self, s, v):
        return (v.real, v.imag)

    def decode(self, s, v):
        return complex(v[0], v[1])


class NDArrayExtension(Extension):

    name = 'ndarray'

    def __init__(self):
        if 'numpy' in sys.modules:
            import numpy as np
            self.cls = np.ndarray

    def match(self, s, v):
        return (hasattr(v, 'shape') and
                hasattr(v, 'dtype') and
                hasattr(v, 'tobytes'))

    def encode(self, s, v):
        return dict(shape=v.shape,
                    dtype=str(v.dtype),
                    data=v.tobytes())

    def decode(self, s, v):
        try:
            import numpy as np
        except ImportError:
            return v
        a = np.frombuffer(v['data'], dtype=v['dtype'])
        a.shape = v['shape']
        return a


standard_extensions = [ComplexExtension, NDArrayExtension]
