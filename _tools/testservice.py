"""
This script provides a service to test BSDF implementations of different
languages. It is written in Python, since BSDF's reference implementation is.

To use, import this module and use ``main(test_dir, *exe)``. The test_dir
will be the current directory when the command is executed. The exe is the
command to run, which should somewhere have placeholders for ``{fname1}``
and ``{fname2}``. The extension of these file names indicates the format
(currently json or bsdf). The command will usually call into a script
(written in a language of choice), which occurs repeatedly during the
test.

Alternatively, one can do a call in the shell:
``python testservice.py dir exe ...``.
One can also run this script using pytest, in which case the tests are run
in-process to allow establishing the test coverage. 

"""

from __future__ import absolute_import, print_function, division

import os
import sys
import time
import json
import random
import tempfile
import threading
import subprocess
from io import open  # pypy and py27 compat

import datagen

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', 'python')))
import bsdf  # the current script is next to this module


## Setup

def setup_module(module):
    """ This gets automatically called by pytest. """
    global exe, exe_name
    exe = []
    exe_name = 'pytest'


def main(test_dir_, *exe_, excludes=None):
    """ We call this when this is run as as script. """
    global test_dir, exe, exe_name, runner
    
    excludes = dict((e, True) for e in (excludes or []))
    # Set exe and test_dir
    test_dir = test_dir_
    exe = list(exe_)
    exe_name = exe[0]
    if not os.path.isdir(test_dir):
        raise RuntimeError('Not a valid directory: %r' % test_dir)
    
    # Run tests
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            print('Running service test %s %s ' % (exe_name, name), end='')
            try:
                func(**excludes)
            except Exception:
                print('  Failed')
                raise
            print('  Passed')


## Helper functions

def invoke_runner(fname1, fname2):
    """ Invoke the runner in a new process to convert the data. """
    
    assert os.path.isfile(fname1)
    
    if exe_name == 'pytest':
        # Shortcut to test with pytest
        data = load(fname1)
        save(fname2, data)
    
    else:
        # Normal sub-process behavior
        exe2 = [e.format(fname1=fname1, fname2=fname2) for e in exe]
        p = subprocess.Popen(exe2, cwd=test_dir,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0 or err:
            rename_as_error(fname1, fname2)
            raise RuntimeWarning('{} failed:\n{}\n{}'.format(exe_name,
                                                             out.decode(errors="replace"),
                                                             err.decode(errors="replace")))
    
    assert os.path.isfile(fname2)


def compare_data(data1, data2):
    """ Compare the data, raise error if it fails. """
    
    if data1 == data2:
        print('.', end='')
        sys.stdout.flush()
    else:
       
        if isinstance(data1, dict) and len(data1) > 0 and len(list(data1.keys())[0]) > 63:
            # Oh silly Matlab, truncate keys, because Matlab does that
            for key in list(data1.keys()):
                data1[key[:63]] = data1[key]
                del data1[key]
        
        if data1 != data2:
            print()
            print('data1:', data1)
            print('data2:', data2)
        
            deep_compare(data1, data2)
            assert data1 == data2  # just in case deep_compare has a bug


def deep_compare(ob1, ob2):
    """ Compare two objects deeply to produce more useful assertions. """
    
    # Allow subtypes, e.g. int/bool
    #assert isinstance(ob1, type(ob2)) or isinstance(ob2, type(ob1)), 'type mismatch:\n{}\nvs\n{}'.format(ob1, ob2)
    assert type(ob1) is type(ob2), 'type mismatch:\n{}\nvs\n{}'.format(ob1, ob2)
    
    if isinstance(ob1, list):
        assert len(ob1) == len(ob2), 'list sizes dont match:\n{}\nvs\n{}'.format(ob1, ob2)
        for sub1, sub2 in zip(ob1, ob2):
            deep_compare(sub1, sub2)
    elif isinstance(ob1, dict):
        assert len(ob1) == len(ob2), 'dict sizes dont match:\n{}\nvs\n{}'.format(ob1, ob2)
        for key1 in ob1:
            assert key1 in ob2,  'dict key not present in dict2:\n{}\nvs\n{}'.format(key1, ob2)
        for key2 in ob2:
            assert key2 in ob1,  'dict key not present in dict1:\n{}\nvs\n{}'.format(key2, ob1)
        for key in ob1:
            deep_compare(ob1[key], ob2[key])
    else:
        assert ob1 == ob2, 'Values do not match:\n{}\nvs\n{}'.format(ob1, ob2)


def convert_data(fname1, fname2, data1):
    """ Convert data, by saving to fname, invoking the runner, and reading back.
    If something goes wrong, the files are saved as error.xx, otherwiser the files
    are cleaned up.
    """
    try:
        save(fname1, data1)
        invoke_runner(fname1, fname2)
        data2 = load(fname2)
        return data2
    except Exception:
        rename_as_error(fname1, fname2)
        print(data1)
        raise
    finally:
        remove(fname1, fname2)


def load(fname):
    """ Load from json or bsdf, depending on the extension. """
    if fname.endswith('.json'):
        with open(fname, 'rt', encoding='utf-8') as f:
            return json.load(f)
    elif fname.endswith('.bsdf'):
        return bsdf.load(fname)
    else:
        assert False


def save(fname, data):
    """ Save to json or bsdf, depending on the extension. """
    if fname.endswith('.json'):
        with open(fname, 'wt', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    elif fname.endswith('.bsdf'):
        bsdf.save(fname, data)
    else:
        assert False

_tempfilecounter = 0

def get_filenames(ext1, ext2):
    """ Get termporary file names. """
    global _tempfilecounter
    d = os.path.join(tempfile.gettempdir(), 'bsdf_tests')
    os.makedirs(d, exist_ok=True)
    fname1 = 'service_test_{}_{}_{}'.format(os.getpid(), threading.get_ident(), _tempfilecounter + 1)
    fname2 = 'service_test_{}_{}_{}'.format(os.getpid(), threading.get_ident(), _tempfilecounter + 2)
    _tempfilecounter += 2
    return os.path.join(d, fname1 + ext1), os.path.join(d, fname2 + ext2)


def rename_as_error(*filenames):
    """ Rename files to error.xx. """
    for fname in filenames:
        try:
            os.replace(fname, os.path.dirname(fname) + '/error.' + fname.rsplit('.')[-1])
        except Exception:
            pass


def remove(*filenames):
    """ Remove multiple filenames. """
    for fname in filenames:
        try:
            os.remove(fname)
        except Exception:
            pass


## The tests

longnames = {}
for n in (249, 250, 251, 252, 253, 254, 255, 256, 259):
    name = ('x%i_' % n) + 'x' * (n-5)
    assert len(name) == n
    longnames[n] = name


JSON_ABLE_OBJECTS = [
    # Basics
    [1,2,3, 4.2, 5.6, 6.001],
    dict(foo=7.2, bar=42, a=False),
    ["hello", 3, None, True, 'there', 'x'],
    
    # Singletons - note that some (e.g. Matlab's) json implementations have trouble having
    # anything else than list/dict as root element, and with empty dicts/structs.
    
    # Some nesting
    [3.2, {'foo': 3, 'bar': [1, 2, [3, {'x':'y'}]]}, [1, [2, [[[None], 4.9], {'spam': 'eggs'}]]], False, True],
    [[[[[[[[[42]]]]]]]]],
    dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=dict(x=42)))))))))))),
    
    # Unicode
    dict(foo='fóó', bar='€50)', more='\'"{}$'),
    
    # Elements with a length near the 250 boundary
    [name for name in longnames.values()],  # long strings
    # [name.encode() for name in longnames.values()],  # long bytes (not jsonable)
    dict((val, key) for key, val in longnames.items()),  # long keys
    dict(('L%i' % n, [n] * n) for n in longnames.keys()),  # long lists
    [dict(('d%i' % i, i) for i in range(n)) for n in longnames.keys()],  # long dicts
    
    # Integers - e.g. JS does not have int64
    [0, -1, -2, 1, 2, 42, -1337,
     -126, -127, -128, -129, -254, -255, -256, -257,  # 8 bit
      126,  127,  128,  129,  254,  255,  256,  257,
     -32766, -32767, -32768, -32769, -65534, -65535, -65536, -65537,  # 16 bit
      32766,  32767,  32768,  32769,  65534,  65535,  65536,  65537,
     -2147483646, -2147483647, -2147483648, -2147483649, -4294967294, -4294967295, -4294967296, -4294967297,  # 32 bit
      2147483646,  2147483647,  2147483648,  2147483649,  4294967294,  4294967295,  4294967296,  4294967297,
     -9007199254740991, 9007199254740991,  # JS Number.MAX_SAFE_INTEGER
     ],
    
    # Floats
    [0.0001, 0.1, 1.1, 100.1, 10000.1]
]


def test_bsdf_to_json(**excludes):
    
    for data1 in JSON_ABLE_OBJECTS:
        fname1, fname2 = get_filenames('.bsdf', '.json')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)


def test_json_to_bsdf(**excludes):
    
    for data1 in JSON_ABLE_OBJECTS:
        fname1, fname2 = get_filenames('.json', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)


def test_bsdf_to_bsdf(**excludes):
    
    # Just repeat these
    for data1 in JSON_ABLE_OBJECTS[:-1]:
        fname1, fname2 = get_filenames('.bsdf', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)
    
    # Singletons, some JSON implementations choke on these
    for data1 in [None, False, True, 3.4, '', 'hello', [], {}, b'', b'xx']:
        fname1, fname2 = get_filenames('.bsdf', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)
        assert str(data1) == str(data2), str((data1, data2))  # because False != 0
    
    for data1 in [0, 1, 0.0, 1.0, 4]:
        fname1, fname2 = get_filenames('.bsdf', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)
        if 'roundfloatisnotint' not in excludes:
            assert str(data1) == str(data2), str((data1, data2))  # because 0.0 != 0
    
    # Special values
    for data1 in [float('nan'), float('inf'), float('-inf')]:
        fname1, fname2 = get_filenames('.bsdf', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        #compare_data(data1, data2)
        assert str(data1) == str(data2)  # because nan != nan
    
    # Use float32 for encoding floats
    fname1, fname2 = get_filenames('.bsdf', '.bsdf')
    data1 = [1,2,3, 4.2, 5.6, 6.001]
    try:
        bsdf.save(fname1, data1, float64=False)
        invoke_runner(fname1, fname2)
        data2 = bsdf.load(fname2)
    except Exception:
        print(data1)
        raise
    finally:
        remove(fname1, fname2)
    assert data1 != data2
    assert all([(abs(d1-d2) < 0.001) for d1, d2 in zip(data1, data2)])
    
    # Test converters using complex number
    fname1, fname2 = get_filenames('.bsdf', '.bsdf')
    data1 = 3 + 4j
    try:
        bsdf.save(fname1, data1)
        invoke_runner(fname1, fname2)
        data2 = bsdf.load(fname2)
    except Exception:
        print(data1)
        raise
    finally:
        remove(fname1, fname2)
    assert isinstance(data2, complex)
    assert data1 == data2
    
    # Deal with unknown converters by leaving data through
    class MyConverter(bsdf.Converter):
        name = 'test.foo'
        cls = threading.Thread
        def encode(self, v):
            return [7, 42]
        def decode(self, v):
            return None
    
    fname1, fname2 = get_filenames('.bsdf', '.bsdf')
    data1 = ['hi', threading.Thread(), 'there']
    try:
        bsdf.save(fname1, data1, [MyConverter])
        invoke_runner(fname1, fname2)
        data2 = bsdf.load(fname2)
    except Exception:
        print(data1)
        raise
    finally:
        remove(fname1, fname2)
    assert data2 == ['hi', [7, 42], 'there']
    
    # Test bytes / blobs
    # We do not test compression in shared tests, since its not a strict requirement
    for data1 in [[3, 4, b'', b'x', b'yyy', 5],
                  [5, 6, bsdf.Blob(b'foo', compression=0, extra_size=20, use_checksum=False), 7],
                  [5, 6, bsdf.Blob(b'foo', compression=0, extra_size=10, use_checksum=True), 7],
                 ]:
        data2 = convert_data(fname1, fname2, data1)
        # Compare, but turn blobs into bytes
        data1 = [x.get_bytes() if isinstance(x, bsdf.Blob) else x for x in data1]
        compare_data(data1, data2)
    
    # Test unclosed stream
    s = bsdf.ListStream()
    data1 = [3, 4, 5, s]
    #
    fname1, fname2 = get_filenames('.bsdf', '.bsdf')
    with open(fname1, 'wb') as f:
        bsdf.save(f, data1)
        s.append(6)
        s.append(7)
    invoke_runner(fname1, fname2)
    data2 = bsdf.load(fname2)
    assert data2 == [3, 4, 5, [6, 7]]


def test_bsdf_to_bsdf_random(**excludes):
    
    # we want pytest to be repeatable
    if exe_name == 'pytest':
        return
    
    # Process a few random dicts
    for iter in range(8):
        random.seed(time.time())
        
        data1 = datagen.random_dict(6, maxn=100, types=datagen.JSON_TYPES)
        fname1, fname2 = get_filenames('.bsdf', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)
    
    # Process a few random lists
    for iter in range(8):
        random.seed(time.time())
        
        data1 = datagen.random_list(6, maxn=100, types=datagen.JSON_TYPES)
        fname1, fname2 = get_filenames('.bsdf', '.bsdf')
        data2 = convert_data(fname1, fname2, data1)
        compare_data(data1, data2)


## Run the tests

if __name__ == '__main__':
    
    # Process CLI arguments
    if len(sys.argv) == 1:
        print(__doc__)
        sys.exit(1)
    elif len(sys.argv) < 3:
        raise RuntimeError('BSDF test service needs at least two arguments (test_dir, exe, ...)')
    test_dir = os.path.abspath(sys.argv[1])
    
    # Call main
    main(test_dir, *sys.argv[2:])
