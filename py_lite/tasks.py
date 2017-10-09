""" Implement tasks for invoke.
"""

import os
import sys
import subprocess
import webbrowser
from invoke import task

this_dir = os.path.dirname(__file__)

def call(*cmd):
    sys.exit(subprocess.call(cmd, cwd=this_dir))


@task
def test_style(ctx):
    """ Run style tests with flake8. """
    # Print nice messages when all is well; flake8 does not celebrate.
    ret_code = subprocess.call(['flake8', 'bsdf_lite.py'], cwd=this_dir)
    if ret_code == 0:
        print('No style errors found')
    sys.exit(ret_code)

@task
def test_unit(ctx):
    """ Run all unit tests with pytest. """
    call('pytest', '-v', '-x', '--cov', 'bsdf', '--cov-report', 'html', '.')

@task
def test_shared(ctx, exe=sys.executable):
    """ Run BSDF tests using the shared test service. Use --exe python34 to specify interpreter."""
    sys.path.insert(0, os.path.join(this_dir, '..', 'py'))
    import bsdf_test_service
    bsdf_test_service.main(this_dir, exe, 'testservice_runner.py', '{fname1}', '{fname2}')

@task
def update_readme(ctx):
    """ Update the reference section in the readme. """
    # Read lines of readme
    lines = open(os.path.join(this_dir, 'README.md'), 'rb').read().decode().rstrip().splitlines()
    lines.append('')
    # Find where the reference is
    i1 = i2 = -1
    for i, line in enumerate(lines):
        if i1 == -1:
            if line.startswith('## Reference'):
                i1 = i
        else:
            if line.startswith('## '):
                i2 = i
    # Inject reference
    if i1 > 0:
        lines = lines[:i1+1] + ['', _get_reference(), ''] + lines[i2:]
    # Write back
    with open(os.path.join(this_dir, 'README.md'), 'wb') as f:
        f.write('\n'.join(lines).encode())


def _get_reference():
    """ Get the reference documentation from the source code.
    """
    sys.path.insert(0, this_dir)
    import bsdf_lite
    import inspect
    
    parts = []
    
    for ob in (bsdf_lite.BsdfLiteSerializer, ):
        
        sig = str(inspect.signature(ob))
        if isinstance(ob, type):
            parts.append('### class {}`{}`\n\n{}\n'.format(ob.__name__, sig, get_doc(ob, 4)))
            for name, method in ob.__dict__.items():
                if not name.startswith('_') and getattr(method, '__doc__', None) and callable(method):
                    sig = str(inspect.signature(method))
                    sig = '(' + sig[5:].lstrip(', ') if sig.startswith('(self') else sig
                    parts.append('#### method {}`{}`\n\n{}\n'.format(name, sig, get_doc(method, 8)))
            parts.append('##')
        else:
            parts.append('### function {}`{}`\n\n{}\n'.format(ob.__name__, sig, get_doc(ob, 4)))
    
    return '\n'.join(parts)


def get_doc(ob, dedent):
    """ Strip and dedent docstrings from an object. """
    lines = ob.__doc__.strip().splitlines()
    for i in range(1, len(lines)):
        lines[i] = lines[i][dedent:]
    lines.append('')
    return '\n'.join(lines)
