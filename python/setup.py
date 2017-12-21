try:
    from setuptools import setup  # Supports wheels
except ImportError:
    from distutils.core import setup  # Supports anything else

import os


version = None
doc = None
fname = os.path.join(os.path.dirname(__file__), 'bsdf.py')
for line in open(fname, 'rb').read().decode('utf-8').splitlines():
    if version is None and line.startswith('VERSION ='):
        parts = line.split('#')[0].split('=')[-1].split(',')
        version = '.'.join(p.strip() for p in parts)
    elif line.startswith('"""'):
        if doc is None:
            doc = line + '\n'
        else:
            doc = doc.strip(' \t\n\r"')
    elif doc and doc.startswith('"""'):
        doc += line + '\n'
        
assert version, 'could not find version'
assert doc, 'could not find docs'


setup(name='bsdf',
      version=version,
      description='Python implementation of the Binary Structured Data Format (BSDF).',
      long_description=doc,
      author='Almar Klein',
      author_email='almar.klein@gmail.com',
      url='http://bsdf.io',
      py_modules=['bsdf', 'bsdf_cli'],
      entry_points={'console_scripts': ['bsdf = bsdf_cli:main']},
     )
