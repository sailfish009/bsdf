#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# bsdf documentation build configuration file. This file is execfile()d
# with the current directory set to its containing dir.


import os
import sys
import subprocess

# Update all readmes first
curdir = os.getcwd()
os.chdir('..')
lines = subprocess.getoutput(['invoke', '-l']).splitlines()
lines = [line.strip().split(' ')[0] for line in lines if line.count('.update-readme')]
for line in lines:
    print(subprocess.getoutput(['invoke', line]))
os.chdir(curdir)

# Generate pages using our own system
sys.path.insert(0, os.path.abspath('.'))
import pages
pages.build(False, True)


# -- General configuration ------------------------------------------------


# General information about the project.
project = 'BSDF'
copyright = '2017, Almar Klein'
author = 'Almar Klein'

# The version info for the project you're documenting
VERSION = (2, 1)
version = '%i.%i' % VERSION  # The short X.Y version.
release = '%i.%i' % VERSION  # The full version, including alpha/beta/rc tags.

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.

html_theme = 'default'  # Let RTD choose

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

html_show_sourcelink = False

# -- More general configuration -------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False
