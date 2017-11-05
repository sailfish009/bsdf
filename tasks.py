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
    ns.add_collection(collection, dname.replace('_', '-'))
    for ob in module.values():
        if isinstance(ob, Task):
            collection.add_task(ob)
        elif isinstance(ob, Collection):
            ns.add_collection(ob)


# Implement collection default messages, without creating an actual task for it
if len(sys.argv) == 2 and sys.argv[1] in ns.collections.keys():
    lines = subprocess.getoutput(['invoke', '-l']).splitlines()
    lines = [line for line in lines if line.strip().startswith(sys.argv[1] + '.')]
    print('Task {} is a category with available tasks:\n'.format(sys.argv[1]))
    print('\n'.join(lines))
    sys.exit(1)

# Add root tasks ...

@ns.add_task
@task(default=True)
def help(ctx):
    """ Get help on BSDF's development workflow. """
    
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

@ns.add_task
@task
def build_pages(ctx, show=False):
    """ Build the BSDF website from the markdown files. """
    
    sys.path.insert(0, os.path.join(ROOT_DIR, '_tools'))
    import pages
    import webbrowser
    
    pages.build()
    if show:
        webbrowser.open(os.path.join(ROOT_DIR, '_pages', 'index.html'))


@ns.add_task
@task
def check_line_endings(ctx, show=False):
    """ Check line endings of all source files. """
    
    for dname in os.listdir(ROOT_DIR):
        if dname.startswith(('.', '_')) or ' ' in dname:
            continue
        dirname = os.path.join(ROOT_DIR, dname)
        if os.path.isfile(dirname):
            _check_line_endings(dirname)
        else:
            for fname in os.listdir(dirname):
                filename = os.path.join(dirname, fname)
                if os.path.isfile(filename) and not fname.startswith('.'):
                    _check_line_endings(filename)
            
def _check_line_endings(filename):
    text = open(filename, 'rb').read().decode()
    if '\r' in text:
        print('Detected \\r in ', filename)
