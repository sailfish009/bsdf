"""
Tests for the CLI
"""

import io
import os
import sys
import time
import random
import tempfile
import subprocess

import bsdf
import bsdf_cli

this_dir = os.path.dirname(__file__)

tempfilename = os.path.join(tempfile.gettempdir(), 'bsdf_cli_test.bsdf')


def run_local(*args):
    ori_argv = sys.argv[1:]
    ori_stdout = sys.stdout
    sys.argv[1:] = args
    sys.stdout = io.StringIO()
    try:
        bsdf_cli.main()
    except SystemExit as err:
        return sys.stdout.getvalue(), err.code
    else:
        return sys.stdout.getvalue(), ''
    finally:
        sys.argv[1:] = ori_argv
        sys.stdout = ori_stdout

def run_remote(*args):
    cmd = [sys.executable, '-m', 'bsdf'] + list(args)
    return subprocess.check_output(cmd, cwd=this_dir).decode().replace('\r\n', '\n')


##


def test_help():
    # Global help can be invoked in a few ways
    r1, e1 = run_local('help')
    r2, e2 = run_local('-h')
    r3, e3 = run_local('--help')
    assert e1 == e2 == e3 == ''
    assert r1 == r2 == r3
    assert 'Binary Structured Data Format' in r1
    assert 'available commands' in r1.lower()
    
    # Test help on a command
    r1, e1 = run_local('help', 'version')
    r2, e2 = run_local('version', '--help')
    assert e1 == e2 == ''
    assert r1 == r2
    assert 'usage: bsdf version' in r1.lower()
    
    # But command needs to exist
    r3, e3 = run_local('help', 'fooo')
    assert not r3
    assert 'fooo' in e3


def test_wrong_commands():
    
    # No command
    r, e = run_local()
    assert not r
    assert 'no command given' in e.lower()
    
    # Nonexisting command
    r, e = run_local('fooo')
    assert not r
    assert 'fooo' in e and 'invalid command' in e.lower()
    
    # Wrong number of args
    r, e = run_local('version', 'foo')
    assert not r
    assert 'positional arguments' in e.lower()
    
    # Wrong kwargs
    r, e = run_local('version', '--foo')
    assert not r
    assert 'unexpected keyword argument' in e.lower()


def test_version():
    r1, e1 = run_local('version')
    r2, e2 = run_local('--version')
    r3, e3 = run_local('-v')
    r4 = run_remote('version')
    
    assert e1 == e2 == e3 == ''
    assert r1 == r2 == r3 == r4 
    
    assert r1.startswith('bsdf.py version ')
    assert r1.strip().split(' ')[-1] == bsdf.__version__


def test_info():
    data1 = [3, 4, 5]
    bsdf.save(tempfilename, data1)
    
    r, e = run_local('info', tempfilename)
    r = r.replace('    ', ' ').replace('  ', ' ').replace('  ', ' ')
    assert not e
    assert 'file_size' in r
    assert 'valid: true' in r
    assert 'version:' in r
    
    # Not a file
    r, e = run_local('info', '~/foo_does_not_exist.bsdf')
    assert not r
    assert 'invalid file' in e
    
    # Not a bsdf file
    with open(tempfilename, 'wb') as f:
        pass
    r, e = run_local('info', tempfilename)
    r = r.replace('    ', ' ').replace('  ', ' ').replace('  ', ' ')
    assert not e
    assert 'file_size' in r
    assert 'valid: false' in r
    assert 'version: ?' in r


def test_create():
    r, e = run_local('create', tempfilename, '[3,4,5]*10')
    data = bsdf.load(tempfilename)
    assert data == [3, 4, 5] * 10


def test_convert():
    tempfilename1 = tempfilename
    tempfilename2 = tempfilename + '.json'
    
    data1 = [4, 5, 6]
    bsdf.save(tempfilename, data1)
    
    # Convert to json
    r, e = run_local('convert', tempfilename1, tempfilename2)
    assert not e
    assert tempfilename2 in r
    
    # Convert back
    r, e = run_local('convert', tempfilename2, tempfilename1)
    assert not e
    assert tempfilename1 in r
    
    # Check
    assert open(tempfilename2, 'rb').read().decode().strip() == '[4, 5, 6]'
    data2 = bsdf.load(tempfilename)
    assert data1 == data2
    
    # Fail, unknown extension
    r, e = run_local('convert', tempfilename1+'.png', tempfilename1)
    assert not r
    assert 'unknown' in e.lower() and 'extension' in e.lower() and 'load' in e
    #
    r, e = run_local('convert', tempfilename1, tempfilename1+'.png')
    assert not r
    assert 'unknown' in e.lower() and 'extension' in e.lower() and 'save' in e
    
    # Cannot convert bytes
    bsdf.save(tempfilename, bsdf.Blob(b'xx'))
    r, e = run_local('convert', tempfilename1, tempfilename2)
    assert not r
    assert 'not JSON serializable' in e
    assert not os.path.isfile(tempfilename2)  # file was deleted/not written


def test_view():
    
    # Create file
    data1 = [1, 2, 3, [4, 4, 4, 4, 4], 8, 9]
    bsdf.save(tempfilename, data1)
    
    # Test content, plain
    r, e = run_local('view', tempfilename)
    assert not e
    assert tempfilename not in r
    assert r.count('4') == 5
    assert '5' in r  # number of elements in inner list
    assert '6' in r  # number of elements in outer list
    
    # Test content, plus info
    r, e = run_local('view', tempfilename, '--info')
    assert not e
    assert tempfilename in r
    assert 'file_size:' in r
    assert r.count('4') >= 5  # can also occur in meta info
    assert '5' in r  # number of elements in inner list
    assert '6' in r  # number of elements in outer list
    
    # Test content, max depth 1
    r, e = run_local('view', tempfilename, '--depth=1')
    assert not e
    assert r.count('4') == 0  # collapsed
    assert '5' in r  # number of elements in inner list
    assert '6' in r  # number of elements in outer list
    
    # Test content, max depth 0
    r, e = run_local('view', tempfilename, '--depth=0')
    assert not e
    assert r.count('\n') == 1  # all collapsed
    assert '5' not in r  # number of elements in inner list
    assert '6' in r  # number of elements in outer list
    
    # Fail - not a file
    r, e = run_local('view', '~/foo_does_not_exist.bsdf')
    assert not r
    assert 'invalid file' in e
    
    # Fail - not a bsdf file
    with open(tempfilename, 'wb') as f:
        pass
    r, e = run_local('view', tempfilename)
    assert not r
    assert 'does not look like a BSDF file' in e
    
    # Fail - major version is off
    bb = bsdf.encode(data1)
    with open(tempfilename, 'wb') as f:
        f.write(bb[:4] + b'\x00' + bb[5:])
    r, e = run_local('view', tempfilename)
    assert r == '' and 'different major version' in e
    
    # Warn - minor version is lower than file
    bb = bsdf.encode(data1)
    with open(tempfilename, 'wb') as f:
        f.write(bb[:5] + b'\xff' + bb[6:])
    r, e = run_local('view', tempfilename)
    assert not e
    assert 'higher minor version' in r
    assert r.count('4') >= 5
    
    # Test string truncation
    too_long = 'x' * 200
    just_right = 'x' + '_' * 38 + 'x'
    data1 = [too_long, just_right]
    bsdf.save(tempfilename, data1)
    r, e = run_local('view', tempfilename)
    assert not e
    assert too_long not in r and ('x'* 39 + u'\u2026') in r
    assert just_right in r
    
    # Test float32 for cov
    data1 = [3.14159, 42.0]
    bsdf.save(tempfilename, data1, float64=False)
    r, e = run_local('view', tempfilename)
    assert not e
    assert '3.14159' in r and '42.0' in r

    # Test unclosed stream
    s = bsdf.ListStream()
    data1 = [3, 4, 5, s]
    #
    with open(tempfilename, 'wb') as f:
        bsdf.save(f, data1)
        s.append(6)
        s.append(7)
    #
    r, e = run_local('view', tempfilename)
    assert not e
    assert '6' in r and '7' in r
    assert 'stream' in r and not '2' in r


def test_view_random():
    
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '_tools')))
    import datagen
    
    types = list(datagen.ALL_TYPES)
    
    # Process a few random dicts
    for iter in range(8):
        random.seed(time.time())
        data1 = datagen.random_dict(6, maxn=100, types=types)
        bsdf.save(tempfilename, data1)
        r, e = run_local('view', tempfilename)
        assert not e
        assert r
        # not much more to assert, except that it does not crash
    
    # Process a few random lists
    for iter in range(8):
        random.seed(time.time())
        data1 = datagen.random_list(6, maxn=100, types=types)
        bsdf.save(tempfilename, data1)
        r, e = run_local('view', tempfilename)
        assert not e
        assert r


if __name__ == '__main__':
    test_help()
    test_wrong_commands()
    test_version()
    test_info()
    test_create()
    test_convert()
    test_view()
    test_view_random()
