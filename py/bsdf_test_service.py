"""
This script provides a service to test BSDF implementations of different
languages. It is written in Python, since BSDF's reference implementation is.

To use, call ``python bsdf_test_service.py dir exe ...``, where ``dir`` is the
directory to test. It should contain a file starting with 'service_runner.'
(any extension) which can be run with ``exe ... service_runner.xx fname1 fname2``.

The service runner script (written in a language of choice) is called
repeatedly during the test. It is given two arguments: the source file to read
and the destination file to write. The extension of these files indicates the
format (currently json or bsdf).

This script can also be run using pytest, in which case the tests are run
in-process to allow establishing the test coverage. 

"""

# todo:
# - unicode names in dict
# - unicode strings
# - strings/lists/names of 251/244/255 chars

import os
import sys
import json
import tempfile
import subprocess
import threading

import bsdf  # the current script is next to this module


## Setup

def setup_module(module):
    """ This gets automatically called by pytest. """
    global runner
    runner = 'pytest'


def main_configure():
    """ We call this when this is run as as script. """
    global test_dir, exe, runner
    
    if len(sys.argv) == 1:
        print(__doc__)
        sys.exit(1)
    elif len(sys.argv) < 3:
        raise RuntimeError('BSDF test service needs at least two arguments (test_dir, exe, ...)')
    
    # Get dir
    test_dir = os.path.abspath(sys.argv[1])
    if not os.path.isdir(test_dir):
        raise RuntimeError('Not a valid directory: %r' % test_dir)
    
    # Get exe (can be multiple args, the service_runner is appended to it)
    exe = list(sys.argv[2:])
    
    # Find service runner
    runners = [os.path.join(test_dir, fname) for fname in os.listdir(test_dir)
            if fname.startswith('service_runner.')]
    if len(runners) == 0:
        raise RuntimeError('Need service_runner.xx in directory %s to test.' % test_dir)
    elif len(runners) > 1:
        raise RuntimeError('Find multiple service runners in %s.' % test_dir)
    else:
        runner = runners[0]


## Helper functions

def invoke_runner(fname1, fname2):
    """ Invoke the runner in a new process to convert the data. """
    
    assert os.path.isfile(fname1)
    
    if runner == 'pytest':
        # Shortcut to test with pytest
        if fname1.endswith('.json'):
            data = json_load(fname1)
        elif fname1.endswith('.bsdf'):
            data = bsdf.load(fname1)
        else:
            assert False
        if fname2.endswith('.json'):
            json_save(fname2, data)
        elif fname2.endswith('.bsdf'):
            bsdf.save(fname2, data)
        else:
           assert False
    
    else:
        # Normal sub-process behavior
        p = subprocess.Popen(exe + [runner, fname1, fname2], cwd=test_dir,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0 or err:
            raise RuntimeWarning(f'{runner} failed:\n{out.decode(errors="replace")}\n{err.decode(errors="replace")}')
    
    assert os.path.isfile(fname2)


def json_load(fname):
    with open(fname, 'rt', encoding='utf-8') as f:
        return json.load(f)


def json_save(fname, data):
    with open(fname, 'wt', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


_tempfilecounter = 0

def get_filenames(ext1, ext2):
    """ Get termporary file names. """
    global _tempfilecounter
    d = os.path.join(tempfile.gettempdir(), 'bsdf_tests')
    os.makedirs(d, exist_ok=True)
    fname1 = f'service_test_{os.getpid()}_{threading.get_ident()}_{_tempfilecounter+1}'
    fname2 = f'service_test_{os.getpid()}_{threading.get_ident()}_{_tempfilecounter+2}'
    _tempfilecounter += 2
    return os.path.join(d, fname1 + ext1), os.path.join(d, fname2 + ext2)


def remove(*filenames):
    for fname in filenames:
        os.remove(fname)


## The tests

longnames = {}
for n in (249, 250, 251, 252, 253, 254, 255, 256, 259):
    name = ('x%i_' % n) + 'x' * (n-5)
    assert len(name) == n
    longnames[n] = name


JSON_ABLE_OBJECTS = [
    # # Basics
    [1,2,3, 4.2, 5.6, 6.001],
    dict(foo=7.2, bar=42, a=False),
    ["hello", 3, None, False, 'there', 'x'],
    
    # Unicode
    dict(foo='fóó', bar='€50)', more='\'"{}$'),
    
    # Elements with a length near the 250 boundary
    [name for name in longnames.values()],  # long strings
    # [name.encode() for name in longnames.values()],  # long bytes (not jsonable)
    dict((val, key) for key, val in longnames.items()),  # long keys
    dict(('L%i' % n, [n] * n) for n in longnames.keys()),  # long lists
    [dict(('d%i' % i, i) for i in range(n)) for n in longnames.keys()],  # long dicts
]


def test_json_to_bsdf():
    
    for data1 in JSON_ABLE_OBJECTS:
    
        fname1, fname2 = get_filenames('.json', '.bsdf')
        try:
            json_save(fname1, data1)
            invoke_runner(fname1, fname2)
            data2 = bsdf.load(fname2)
            remove(fname1, fname2)
        except Exception:
            print(data1)
            raise
        
        # assert data1 == data2
        if data1 == data2:
            print('.', end='')
            sys.stdout.flush()
        else:
            print('data1:', data1)
            print('data2:', data2)
            assert data1 == data2


def test_bsdf_to_json():
    for data1 in JSON_ABLE_OBJECTS:
        
        try:
            fname1, fname2 = get_filenames('.bsdf', '.json')
            bsdf.save(fname1, data1)
            invoke_runner(fname1, fname2)
            data2 = json_load(fname2)
            remove(fname1, fname2)
        except Exception:
            print(data1)
            raise
        
        # assert data1 == data2
        if data1 == data2:
            print('.', end='')
            sys.stdout.flush()
        else:
            print('data1:', data1)
            print('data2:', data2)
            assert data1 == data2


def test_bsdf_to_bsdf():
    pass


def test_bsdf_to_bsdf_random():
    pass


## Run the tests

if __name__ == '__main__':
    
    main_configure()
    
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            print('Running service test %s ' % name, end='')
            try:
                func()
            except Exception:
                print('  Failed')
                raise
            print('  Passed')
