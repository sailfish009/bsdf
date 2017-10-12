""" Implement tasks for invoke.
"""

import os
import sys
import subprocess
from invoke import task

this_dir = os.path.dirname(__file__)

def call(*cmd):
    sys.exit(subprocess.call(cmd, cwd=this_dir))


def get_node_exe():
    node_exe = 'nodejs'
    try:
        subprocess.check_output([node_exe, '--version'])
    except Exception:
        node_exe = 'node'
    return node_exe


@task
def test_shared(ctx):
    """ Run BSDF tests on JS using the shared test service. """
    sys.path.insert(0, os.path.join(this_dir, '..', '_tools'))
    import testservice
    exe = get_node_exe()
    testservice.main(this_dir, exe, 'testservice_runner.js', '{fname1}', '{fname2}',
                     excludes=['roundfloatisnotint'])


@task
def test_unit(ctx):
    """ Run unit tests for JS BSDF implementation. """
    exe = get_node_exe()
    call(exe, 'test_unit.js')
