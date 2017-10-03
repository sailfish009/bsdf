""" Script that defines (and collects from subdirs) tasks for invoke. 
"""

import os
import sys
import subprocess

from invoke import Collection, Task, task


# Get root directory of the package
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Init collection; invoke picks this up as the main "list of tasks"
ns = Collection()

# Collect tasks from sub directories
for dname in os.listdir(ROOT_DIR):
    filename = os.path.join(ROOT_DIR, dname, 'tasks.py')
    if not os.path.isfile(filename):
        continue
    
    # Load the module, simulate importing it
    os.chdir(os.path.join(ROOT_DIR, dname))
    module = {'__file__': filename, '__name__': 'tasks'}
    exec(open(filename, 'rb').read().decode(), module)
    os.chdir(ROOT_DIR)
    
    # Add all tasks from this subdir
    collection = Collection()
    ns.add_collection(collection, dname)
    for ob in module.values():
        if isinstance(ob, Task):
            collection.add_task(ob)
        elif isinstance(ob, Collection):
            ns.add_collection(ob)

# Implement collection default messages, without creating an actual task for it
if len(sys.argv) == 2 and sys.argv[1] in ('py', 'matlab'):
    print('Task "%s" is a collection; use "invoke -l" to see available tasks.' % sys.argv[1])
    sys.exit(1)

# Add root help task
@ns.add_task
@task(default=True)
def help(ctx):
    """ Get help on BSDF's development workflow."""
    
    print("""BSDF development workflow
    
    BSDF uses the "invoke" utility to make it easy to invoke tasks such
    as tests. Invoke is a Python utility, so the tasks are defined in
    Python, but most tasks consist of a specific CLI command.
    
    You can cd into each sub directory and use invoke to execute tasks specific
    for that subdir. Use "invoke -l" to get a list of available tasks.
    
    Alternatively, you can use invoke from the root directory in which case
    each task is prefixed with the subdir's name.
    
    Get started by typing "invoke -l".
    """)
