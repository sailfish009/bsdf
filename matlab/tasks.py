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
def test_service(ctx):
    """ Run BSDF tests using the test service. """
    call('python', '../py/bsdf_test_service.py', '.', 'octave-cli')
