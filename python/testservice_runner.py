"""
This little script gets called in a subprcess by the BSDF test service,
with the name of a source file and the name of the file that this script
should produce. The extensions of these files tell us what to do.
"""

import os
import sys
import json
from io import open  # pypy and py27 compat

import bsdf


# Get filenames
fname1 = sys.argv[1]
fname2 = sys.argv[2]
assert os.path.isfile(fname1)
assert not os.path.isfile(fname2)

# Read data
if fname1.endswith('.json'):
    with open(fname1, 'rt', encoding='utf-8') as f:
        data = json.load(f)
elif fname1.endswith('.bsdf'):
    data = bsdf.load(fname1)
else:
    raise NotImplementedError()

# Write data
if fname2.endswith('.json'):
    okw = dict(mode='wt', encoding='utf-8')
    okw = dict(mode='wb') if sys.version_info < (3, ) else okw
    with open(fname2, **okw) as f:
        json.dump(data, f)
elif fname2.endswith('.bsdf'):
    bsdf.save(fname2, data)
else:
    raise NotImplementedError()
