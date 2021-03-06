"""
This little script gets called in a subprcess by the BSDF test service,
with the name of a source file and the name of the file that this script
should produce. The extensions of these files tell us what to do.
"""

import os
import sys
import json

import bsdf_lite

s = bsdf_lite.BsdfLiteSerializer()


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
    with open(fname1, 'rb') as f:
        data = s.load(f)
else:
    raise NotImplementedError()

# Write data
if fname2.endswith('.json'):
    with open(fname2, 'wt', encoding='utf-8') as f:
        json.dump(data, f)
elif fname2.endswith('.bsdf'):
    with open(fname2, 'wb') as f:
        s.save(f, data)
else:
    raise NotImplementedError()
