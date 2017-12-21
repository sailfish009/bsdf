#!/usr/bin/env python
# This file is distributed under the terms of the 2-clause BSD License.
# Copyright (c) 2017, Almar Klein

"""
Implements the command line interface for BSDF,
which is generally invoked when running bsdf.py as a script.
See http://bsdf.io for more information.
"""


from __future__ import absolute_import, division, print_function

import json
import os
import struct
import sys
import time
from io import open  # pypy and py27 compat

import bsdf

strunpack = struct.unpack


def main():

    # Is the command given?
    if len(sys.argv) < 2:
        return fail("No command given. Use 'bsdf help' to get started.")

    # Special cases
    if sys.argv[1] in ('-h', '--help'):
        return cmd_help()
    if sys.argv[1] in ('-v', '--version'):
        return cmd_version()

    # Is the command valid?
    command = sys.argv[1]
    func = globals().get('cmd_' + command, None)
    if func is None:
        return fail('Invalid command: %r' % command)

    # Collect options
    args = []
    kwargs = {}
    for arg in sys.argv[2:]:
        if arg.startswith('--'):
            name = arg[2:].split('=')[0]
            value = arg.split('=', 1)[-1] or True
            kwargs[name] = value
        else:
            args.append(arg)

    # Special case
    if 'help' in kwargs:
        return cmd_help(command)

    # Call
    try:
        func(*args, **kwargs)
    except Exception as err:
        m = str(err)
        if isinstance(err, TypeError) and m.startswith(func.__name__):
            # Show signature mismatch in nice way
            fn = func.__name__
            m = m.replace(fn + '()', fn).replace(fn, 'command "%s"' % command)
        return fail(m)


def fail(msg):
    m = 'BSDF CLI:\n  ' + msg
    sys.exit(m)


def cmd_help(command=None):
    """ Show the help text.

    Usage: bsdf help [command]

    Positional argumens:
      command - (optional) The command to give information for.
    """

    # Show help for specific command
    if command is not None:
        func = globals().get('cmd_' + command, None)
        if func is None:
            fail('Cannot give help for invalid command: %r' % command)
        print(func.__doc__.strip())
        return

    # Otherwise, show generic help
    commands = []
    for name, val in globals().items():
        if name.startswith('cmd_'):
            commands.append((name[4:], val.__doc__.split('\n')[0].strip()))

    commands.sort()
    longest = max([len(c[0]) for c in commands])

    lines = ['Command line interface for the Binary Structured Data Format.',
             'See http://bsdf.io for more information on BSDF.',
             '',
             'usage: bsdf command [options]',
             '',
             'Available commands:',
             ]
    for name, msg in commands:
        lines.append('  ' + name.ljust(longest) + ' - ' + msg)
    lines.append('')
    lines.append("Run 'bsdf help command' "
                 "or 'bsdf command --help' to learn more.")

    print('\n'.join(lines))


def cmd_version():
    """ Print the version of the current Python implementation.

    Usage: bsdf version
    """
    module_name = bsdf.__name__ + '.py'
    version_string = '.'.join([str(i) for i in bsdf.VERSION])
    print('%s version %s' % (module_name, version_string))


def cmd_info(filename):
    """ Print meta information about the given BSDF file.

    Usage: bsdf info filename
    """

    if filename.startswith('~'):
        filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
        fail('Cannot get info for invalid file: %r' % filename)

    # Get version
    with open(filename, 'rb') as f:
        f4 = f.read(4)
        if f4 != b'BSDF':
            is_valid = False
            file_version = '?'
        else:
            is_valid = True
            major_version = struct.unpack('<B', f.read(1))[0]
            minor_version = struct.unpack('<B', f.read(1))[0]
            file_version = '%i.%i' % (major_version, minor_version)

    # Summarize info
    s = os.stat(filename)
    mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s.st_mtime))
    lines = ['file_name:     %s' % os.path.basename(filename),
             'file_size:     %i' % s.st_size,
             'file_mtime:    %s' % mtime,
             'is_valid:      %s' % str(is_valid).lower(),
             'file_version:  %s' % file_version,
             ]

    # Print info
    lines = ['  ' + line for line in lines]
    lines.insert(0, 'BSDF info for: ' + os.path.abspath(filename))
    print('\n'.join(lines))


def cmd_create(filename, code):
    """ Create a BSDF file from data obtained by evaluation Python code.

    Usage: bsdf filename code

    examples:
      bsdf foo.bsdf {meaning:42}
      bsdf bar.bsdf [3,4]*100

    """
    try:
        data = eval(code)
    except Exception as err:
        raise Exception('Could not evaluate Python code to generate data:'
                        '\n  ' + str(err))
    bsdf.save(filename, data)


def cmd_convert(filename1, filename2):
    """ Convert one format into another (e.g. JSON to BSDF).

    Formats currently supported are: JSON, BSDF.
    Note that conversion might fail (e.g. JSON does not support binary blobs).

    Usage: bsdf convert filename1 filename2

    File types are derived from the extensions.
    """
    fname1 = filename1.lower()
    fname2 = filename2.lower()

    if fname1.endswith('.json'):
        with open(filename1, 'rt', encoding='utf-8') as f:
            data = json.load(f)
    elif fname1.endswith('.bsdf'):
        with open(filename1, 'rb') as f:
            data = bsdf.load(f)
    else:
        fail('Unknown load format extension for %r' % filename1)

    try:
        if fname2.endswith('.json'):
            okw = dict(mode='wt', encoding='utf-8')
            okw = dict(mode='wb') if sys.version_info < (3, ) else okw
            with open(filename2, **okw) as f:
                json.dump(data, f)
        elif fname2.endswith('.bsdf'):
            with open(filename2, 'wb') as f:
                bsdf.save(f, data)
        else:
            fail('Unknown save format extension for %r' % filename1)
    except Exception:
        try:
            os.remove(filename2)
        except Exception:  # pragma: no cover
            pass
        raise

    print('Wrote', filename2)


def cmd_view(filename, depth=1e9, info=False):
    """ View the content of a given BSDF file.

    Prints a summary of the content of the given file. This is intended
    for visual inspection; long strings are truncated, and a summary
    is given for binary blobs.

    Note: the output formatting may change, as well as the kind of interaction,
    e.g. support to scroll and jump through the file may be added. Perhaps this
    will pup up a UI at some point.

    Usage: bsdf view filename [options]

    Options:
      --depth=n - The maximum depth to show.
      --info    - Also print meta information about the file.
    """

    if filename.startswith('~'):
        filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
        fail('Cannot view invalid file: %r' % filename)

    if info:
        cmd_info(filename)
        print('')

    with open(filename, 'rb') as f:

        f4 = f.read(4)
        if f4 != b'BSDF':
            fail('This does not look like a BSDF file: %r' % f4)
        # Check version
        major_version = strunpack('<B', f.read(1))[0]
        minor_version = strunpack('<B', f.read(1))[0]
        file_version = '%i.%i' % (major_version, minor_version)
        if major_version != bsdf.VERSION[0]:  # major version should be 2
            t = ('Reading file with different major version (%s) '
                 'from the implementation (%s).')
            fail(t % (bsdf.__version__, file_version))
        if minor_version > bsdf.VERSION[1]:  # minor should be < ours
            t = ('Warning: reading file with higher minor version (%s) '
                 'than the implementation (%s).')
            print(t % (bsdf.__version__, file_version))

        _view_decode(f, 0, int(depth))


def _view_decode(f, depth, maxdepth, noindent=False):
    """ Variant of decode that prints data instead of loading the data.
    Here we see the power of simplicity that comes with BSDF; this function
    is less than 150 lines of code, yet it supports the full BSDF spec.
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
        ext_id = f.read(n).decode('UTF-8')
        ext_id = ' (%s)' % ext_id
    else:
        ext_id = ''

    def printval(s):
        if depth <= maxdepth:
            indent = '' if noindent else '  ' * depth
            print(indent + s + ext_id)

    def printraw(s, **kwargs):
        if depth <= maxdepth:
            indent = '  ' * depth
            print(indent + s, **kwargs)

    if c == b'v':
        printval('null')
    elif c == b'y':
        printval('true')
    elif c == b'n':
        printval('false')
    elif c == b'h':
        value = strunpack('<h', f.read(2))[0]
        printval(str(value))
    elif c == b'i':
        value = strunpack('<q', f.read(8))[0]
        printval(str(value))
    elif c == b'f':
        value = strunpack('<f', f.read(4))[0]
        printval(str(value))
    elif c == b'd':
        value = strunpack('<d', f.read(8))[0]
        printval(str(value))
    elif c == b's':
        n_s = strunpack('<B', f.read(1))[0]
        if n_s == 253: n_s = strunpack('<Q', f.read(8))[0]  # noqa
        value = f.read(n_s).decode('UTF-8')
        if len(value) > 40:
            value = value[:39] + u'\u2026'
        printval(repr(value))
    elif c == b'l':
        n = strunpack('<B', f.read(1))[0]
        if n == 255:
            # Streaming
            n = strunpack('<Q', f.read(8))[0]  # zero if not closed
            printval('[ open list stream ' + ' ]' * (depth >= maxdepth))
            try:
                while True:
                    _view_decode(f, depth + 1, maxdepth)
            except EOFError:
                pass
        else:
            # Normal
            t = 'list with %i elements'
            if n == 253:
                n = strunpack('<Q', f.read(8))[0]  # noqa
            elif n == 254:
                n = strunpack('<Q', f.read(8))[0]
                t = 'closed list stream with %i elements'
            printval('[ ' + t % n + ' ]' * (depth >= maxdepth))
            for i in range(n):
                _view_decode(f, depth + 1, maxdepth)
        if depth < maxdepth:
            printraw(']')
    elif c == b'm':
        n = strunpack('<B', f.read(1))[0]
        if n == 253: n = strunpack('<Q', f.read(8))[0]  # noqa
        printval('{ mapping with %i items' % n + ' }' * (depth >= maxdepth))
        for i in range(n):
            n_name = strunpack('<B', f.read(1))[0]
            if n_name == 253: n_name = strunpack('<Q', f.read(8))[0]  # noqa
            assert n_name > 0
            name = f.read(n_name).decode('UTF-8')
            if depth < maxdepth:
                printraw('  ' + name + ': ', end='')
            _view_decode(f, depth + 1, maxdepth, True)  # no indent
        if depth < maxdepth:
            printraw('}')
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
        checksum = 'none'
        if has_checksum:  # pragma: no cover
            checksum = f.read(16)  # noqa - not used yet
        # Skip alignment
        alignment = strunpack('<B', f.read(1))[0]
        f.read(alignment)
        # Skip data
        f.seek(used_size, 1)
        # Skip remaining space
        f.seek(allocated_size - used_size, 1)
        # Print
        printval('Binary blob size %i/%i/%i compr %i checksum %s' %
                 (allocated_size, used_size, data_size, compression, checksum))
    else:  # pragma: no cover
        raise RuntimeError('Parse error %r' % char)


if __name__ == '__main__':  # pragma: no cover
    main()
