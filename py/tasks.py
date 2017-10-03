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
def style(ctx):
    """ Run style tests with flake8. """
    call('flake8', '.')

@task
def test_unit(ctx):
    """ Run all unit tests with pytest. """
    call('pytest', '-v', '-x', '--cov', 'bsdf', '--cov-report', 'html', '.')

@task
def test_service(ctx):
    """ Run service test in-process to collect its coverage. """
    call('pytest', '-v', '-x', '--cov', 'bsdf', '--cov-report', 'html', 'bsdf_test_service.py')

@task
def test_cov(ctx):
    """ Run service test in-process to collect its coverage. """
    call('pytest', '-v', '-x', '--cov', 'bsdf', '--cov-report', 'html', 'bsdf_test_service.py')

@task
def show_cov(ctx):
    """ Show coverage report in HTML page. """
    webbrowser.open(os.path.join(this_dir, 'htmlcov', 'index.html'))
