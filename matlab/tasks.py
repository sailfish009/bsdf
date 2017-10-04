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
def test_shared(ctx, octave=False, matlab=False):
    """ Run BSDF tests using the shared test service. Use with either --octave or --matlab flag."""
    
    sys.path.insert(0, os.path.join(this_dir, '..', 'py'))
    import bsdf_test_service
    
    if octave and matlab:
        sys.exit('Choose either --octave or --matlab, not both.')
    elif octave:
        bsdf_test_service.main(this_dir, 'octave-cli', '--eval',
                               'service_runner(\'{fname1}\', \'{fname2}\');')
    elif matlab:
        bsdf_test_service.main(this_dir, 'matlab',
                               '-nodisplay', '-nosplash', '-nodesktop', '-wait', '-r',
                               'service_runner(\'{fname1}\', \'{fname2}\');exit();')
    else:
        sys.exit('Choose either --octave or --matlab.')
