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
def test_shared(ctx):
    """ Run BSDF tests on JS using the shared test service. """
    sys.path.insert(0, os.path.join(this_dir, '..', '_tools'))
    import testservice
    testservice.main(this_dir, 'node', 'testservice_runner.js', '{fname1}', '{fname2}')

@task
def test_unit(ctx):
    """ Run unit tests for JS BSDF implementation. """
    call('node', 'test_unit.js')
