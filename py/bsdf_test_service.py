"""
This script provides a service to test BSDF implementations of different
languages. It is written in Python, since BSDF's reference implementation is.

To use, call ``python bsdf_test_service.py exe dir``, where ``dir`` is the
directory to test. It should contain a file starting with 'service_runner.'
(any extension) which can be run with the provided ``exe``.

The service runner script (written in a language of choice) is called
repeatedly during the test. It is given two arguments: the source file to read
and the destination file to write. The extension of these files indicates the
format (currently json or bsdf).

"""

import os
import sys
import json
import tempfile
import subprocess
import threading

import bsdf  # the current script is next to this module


if len(sys.argv) == 1:
    print(__doc__)
    sys.exit(1)
elif len(sys.argv) != 3:
    raise RuntimeError('BSDF test service needs two arguments (exe, and the dir to test)')

# Get exe
exe = sys.argv[1]

# Get dir
test_dir = os.path.abspath(sys.argv[2])
if not os.path.isdir(test_dir):
    raise RuntimeError('Not a valid directory: %r' % test_dir)

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
    assert os.path.isfile(fname1)
    
    p = subprocess.Popen([exe, runner, fname1, fname2], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeWarning(f'{runner} failed:\n{out.decode()}\n{err.decode()}')
    assert os.path.isfile(fname2)

_tempfilecounter = 0

def get_filenames(ext1, ext2):
    global _tempfilecounter
    d = tempfile.gettempdir()
    fname1 = f'bsdf_service_test_{os.getpid()}_{threading.get_ident()}_{_tempfilecounter+1}'
    fname2 = f'bsdf_service_test_{os.getpid()}_{threading.get_ident()}_{_tempfilecounter+2}'
    _tempfilecounter += 2
    return os.path.join(d, fname1 + ext1), os.path.join(d, fname2 + ext2)

def remove(*filenames):
    for fname in filenames:
        os.remove(fname)

## The tasks

JSON_ABLE_OBJECTS = [
    [1,2,3],
    dict(foo=7.2, bar=42),
    ["hello", 3, None, False, 'there'],
]


def task_json_to_bsdf():
    
    for data1 in JSON_ABLE_OBJECTS:
    
        fname1, fname2 = get_filenames('.json', '.bsdf')
        with open(fname1, 'wt') as f:
            json.dump(data1, f)
        invoke_runner(fname1, fname2)
        data2 = bsdf.load(fname2)
        remove(fname1, fname2)
        
        assert data1 == data2
        print('.', end='')


def task_bsdf_to_json():
    for data1 in JSON_ABLE_OBJECTS:
    
        fname1, fname2 = get_filenames('.bsdf', '.json')
        bsdf.save(fname1, data1)
        invoke_runner(fname1, fname2)
        with open(fname2, 'rt') as f:
            data2 = json.load(f)
        remove(fname1, fname2)
        
        assert data1 == data2
        print('.', end='')


def task_bsdf_to_bsdf():
    pass


def task_bsdf_to_bsdf_random():
    pass


## Run the tests

for name, func in list(globals().items()):
    if name.startswith('task_'):
        print('Running service test %s ' % name, end='')
        try:
            func()
        except Exception:
            print('  Failed')
            raise
        print('  Passed')
