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
    install_requires = [],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    platforms = 'any',
    entry_points={'console_scripts': ['bsdf = bsdf_cli:main']},
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        ],
     )
