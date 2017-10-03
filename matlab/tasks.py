""" Implement tasks for invoke.
"""

import os
import sys
import subprocess
from invoke import task

this_dir = os.path.dirname(__file__)

def call(*cmd):
    sys.exit(subprocess.call(cmd, cwd=this_dir))


@task
def test_shared(ctx, exe='octave-cli'):
    """ Run BSDF tests using the shared test service. """
    sys.path.insert(0, os.path.join(this_dir, '..', 'py'))
    import bsdf_test_service
    bsdf_test_service.main(this_dir, exe)
    #call('python', '../py/bsdf_test_service.py', '.', 'octave-cli')
