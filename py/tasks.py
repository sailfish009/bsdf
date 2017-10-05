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
    ret_code = subprocess.call(['flake8', 'bsdf.py'], cwd=this_dir)
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
def test_shared_pytest(ctx):
    """ Run service test in-process to collect its coverage. """
    call('pytest', '-v', '-x', '--cov', 'bsdf', '--cov-report', 'html', 'bsdf_test_service.py')

@task
def show_cov(ctx):
    """ Show coverage report in HTML page (generated by test_unit or test_shared_local). """
    webbrowser.open(os.path.join(this_dir, 'htmlcov', 'index.html'))
