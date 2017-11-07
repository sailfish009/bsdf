# Copyright (c) 2017, Almar Klein
# This file is freely distributed under the terms of the 2-clause BSD License.

"""
Python implementation of the Binary Structured Data Format (BSDF).

BSDF is a binary format for serializing structured (scientific) data.
Read more at https://gitlab.com/almarklein/bsdf.

This is a lite (i.e minimal) variant of the Python implementation. Intended for
easy incorporation in projects, and as a demonstration how simple
a BSDF implementation can be.

This module has no dependencies and works on Python 3.4+.
"""

import sys
import bz2
import hashlib
import logging
import struct
import zlib
from io import BytesIO

logger = logging.getLogger(__name__)


version_info = 2, 0, 0
format_version = version_info[:2]
__version__ = '.'.join(str(i) for i in version_info)


# %% The encoder and decoder implementation


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
    else:
        return spack('<BQ', 253, x)


# Include len decoder for completeness; we've inlined it for performance.
def lendecode(f):
    """ Decode an unsigned integer from a file.
    """
    n = strunpack('<B', f.read(1))[0]
    if n == 253: n = strunpack('<Q', f.read(8))[0]  # noqa
    return n


class BsdfLiteSerializer(object):
    """ Instances of this class represent a BSDF encoder/decoder.

    This is a lite variant of the Python BSDF serializer. It does not support
    lazy loading or streaming, but is otherwise fully functional, including
    support for custom extensions.

    It acts as a placeholder for a set of extensions and encoding/decoding
    options. Options for encoding:

    * compression (int or str): ``0`` or "no" for no compression (default),
      ``1`` or "zlib" for Zlib compression (same as zip files and PNG), and
      ``2`` or "bz2" for Bz2 compression (more compact but slower writing).
      Note that some BSDF implementations (e.g. JavaScript) may not support
      compression.
    * use_checksum (bool): whether to include a checksum with binary blobs.
    * float64 (bool): Whether to write floats as 64 bit (default) or 32 bit.

    """

    def __init__(self, extensions=None, **options):
        self._extensions = {}  # name -> extension
        self._extensions_by_cls = {}  # cls -> (name, extension.encode)
        if extensions is None:
            extensions = standard_extensions
        for extension in extensions:
            self.add_extension(extension)
        self._parse_options(**options)

    def _parse_options(self, compression=0, use_checksum=False, float64=True):

        # Validate compression
        if isinstance(compression, str):
            m = {'no': 0, 'zlib': 1, 'bz2': 2}
            compression = m.get(compression.lower(), compression)
        if compression not in (0, 1, 2):
            raise TypeError('Compression must be 0, 1, 2, '
                            '"no", "zlib", or "bz2"')
        self._compression = compression

        # Other encoding args
        self._use_checksum = bool(use_checksum)
        self._float64 = bool(float64)

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
            if not isinstance(cls, type):
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

        if extension_id is not None:
            bb = extension_id.encode('UTF-8')
            extension_patch = lencode(len(bb)) + bb
            x = lambda i: i.upper() + extension_patch  # noqa
        else:
            x = lambda i: i  # noqa

        if value is None:
            f.write(x(b'v'))  # V for void
        elif value is True:
            f.write(x(b'y'))  # Y for yes
        elif value is False:
            f.write(x(b'n'))  # N for no
        elif isinstance(value, int):
            if -32768 <= value <= 32767:
                f.write(x(b'h') + spack('h', value))  # H for ...
            else:
                f.write(x(b'i') + spack('<q', value))  # I for int
        elif isinstance(value, float):
            if self._float64:
                f.write(x(b'd') + spack('<d', value))  # D for double
            else:
                f.write(x(b'f') + spack('<f', value))  # f for float
        elif isinstance(value, str):
            bb = value.encode('UTF-8')
            f.write(x(b's') + lencode(len(bb)))  # S for str
            f.write(bb)
        elif isinstance(value, (list, tuple)):
            f.write(x(b'l') + lencode(len(value)))  # L for list
            for v in value:
                self._encode(f, v, streams, None)
        elif isinstance(value, dict):
            f.write(x(b'm') + lencode(len(value)))  # M for mapping
            for key, v in value.items():
                assert key.isidentifier()
                name_b = key.encode('UTF-8')
                f.write(lencode(len(name_b)))
                f.write(name_b)
                self._encode(f, v, streams, None)
        elif isinstance(value, bytes):
            f.write(b'b')  # B for blob
            # Compress
            compression = self._compression
            if compression == 0:
                compressed = value
            elif compression == 1:
                compressed = zlib.compress(value)
            elif compression == 2:
                compressed = bz2.compress(value)
            else:
                assert False, 'Unknown compression identifier'
            # Get sizes
            data_size = len(value)
            used_size = len(compressed)
            extra_size = 0
            allocated_size = used_size + extra_size
            # Write sizes - write at least in a size that allows resizing
            if allocated_size <= 250 and compression == 0:
                f.write(spack('<B', allocated_size))
                f.write(spack('<B', used_size))
                f.write(lencode(data_size))
            else:
                f.write(spack('<BQ', 253, allocated_size))
                f.write(spack('<BQ', 253, used_size))
                f.write(spack('<BQ', 253, data_size))
            # Compression and checksum
            f.write(spack('B', compression))
            if self._use_checksum:
                f.write(b'\xff' + hashlib.md5(compressed).digest())
            else:
                f.write(b'\x00')
            # Byte alignment (only necessary for uncompressed data)
            if compression == 0:
                alignment = (f.tell() + 1) % 8  # +1 for the byte to write
                f.write(spack('<B', alignment))  # padding for byte alignment
                f.write(b'\x00' * alignment)
            else:
                f.write(spack('<B', 0))
            # The actual data and extra space
            f.write(compressed)
            f.write(b'\x00' * (allocated_size - used_size))
        else:
            # Try if the value is of a type we know
            x = self._extensions_by_cls.get(value.__class__, None)
            # Maybe its a subclass of a type we know
            if x is None:
                for name, c in self._extensions.items():
                    if c.match(value):
                        x = name, c.encode
                        break
                else:
                    x = None
            # Success or fail
            if x is not None:
                extension_id2, extension_func = x
                if extension_id == extension_id2:
                    raise ValueError('Circular recursion in extension func!')
                self._encode(f, extension_func(value),
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
                checksum = f.read(16)  # noqa - not used yet
            # Skip alignment
            alignment = strunpack('<B', f.read(1))[0]
            f.read(alignment)
            # Get data
            compressed = f.read(used_size)
            # Skip remaining space
            f.read(allocated_size - used_size)
            # Decompress
            if compression == 0:
                value = compressed
            elif compression == 1:
                value = zlib.decompress(compressed)
            elif compression == 2:
                value = bz2.decompress(compressed)
            else:
                raise RuntimeError('Invalid compression %i' % compression)
        else:
            raise RuntimeError('Parse error %r' % char)

        # Convert value if we have a nextension for it
        if extension_id is not None:
            extension = self._extensions.get(extension_id, None)
            if extension is not None:
                value = extension.decode(value)
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
        if f.read(4) != b'BSDF':
            raise RuntimeError('This does not look a BSDF file.')
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


# %% Standard extensions

# Defining extensions as a dict would be more compact and feel lighter, but
# that would only allow lambdas, which is too limiting, e.g. for ndarray
# extension.

class Extension:
    """ Base extension class to implement BSDF extensions for special data types.

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

    * `match(value) -> bool`: return whether the extension can convert the
      given value. The default is ``isinstance(value, self.cls)``.
    * `encode(value) -> encoded_value`: the function to encode a value to
      more basic data types.
    * `decode(encoded_value) -> value`: the function to decode an encoded value
      back to its intended representation.

    """

    name = ''
    cls = ()

    def __repr__(self):
        return '<BSDF extension %r at 0x%s>' % (self.name, hex(id(self)))

    def match(self, v):
        return isinstance(v, self.cls)

    def encode(self, v):
        return v

    def decode(self, v):
        return v


class ComplexExtension(Extension):

    name = 'c'
    cls = complex

    def encode(self, v):
        return (v.real, v.imag)

    def decode(self, v):
        return complex(v[0], v[1])


class NDArrayExtension(Extension):

    name = 'ndarray'

    def __init__(self):
        if 'numpy' in sys.modules:
            import numpy as np
            self.cls = np.ndarray

    def match(self, v):
        return hasattr(v, 'shape') and hasattr(v, 'dtype') and hasattr(v, 'tobytes')

    def encode(self, v):
        return dict(shape=v.shape,
                    dtype=str(v.dtype),
                    data=v.tobytes())

    def decode(self, v):
        try:
            import numpy as np
        except ImportError:
            return v
        a = np.frombuffer(v['data'], dtype=v['dtype'])
        a.shape = v['shape']
        return a


standard_extensions = [ComplexExtension, NDArrayExtension]
