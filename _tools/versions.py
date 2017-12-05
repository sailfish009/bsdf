"""
Script to validate that the version numbers used in the spec, docs, and
implementations match up.
"""

import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


def collect_files():
    """ Collect files that must specify the BSDF version.
    """
    files = []
    
    # Add spec conf
    files.append(os.path.join(ROOT_DIR, 'SPEC.md'))
    
    # Add docs conf
    files.append(os.path.join(ROOT_DIR, '_docs', 'conf.py'))
    
    # Add file for each implementation
    for dname in os.listdir(ROOT_DIR):
        filename = os.path.join(ROOT_DIR, dname, 'tasks.py')
        if not os.path.isfile(filename):
            continue
        # Try name that exactly matches bsdf
        for fname in os.listdir(os.path.join(ROOT_DIR, dname)):
            if fname.split('.')[0].lower() == 'bsdf':
                files.append(os.path.join(ROOT_DIR, dname, fname))
                break
        else:
            # Maybe it has a suffix then?
            for fname in os.listdir(os.path.join(ROOT_DIR, dname)):
                if fname.split('_')[0].lower() == 'bsdf':
                    files.append(os.path.join(ROOT_DIR, dname, fname))
                    break
            else:
                # Not found!
                raise RuntimeError('Could not find BSDF implementation file for ' + dname)
    
    return files


def get_version(filename):
    """ Try to obtain the version tuple from the given filename.
    """
    # Collect lines that seem to define VERSION
    # * starts with "VERSION "
    # * has "=" in it
    lines = []
    for line in open(filename, 'rb').read().decode().splitlines():
        line = line.lstrip()
        if line.startswith('VERSION '):
            raw = ''.join(c if c in '0123456789=' else ' ' for c in line[7:])
            if raw.startswith((' =', '  =')):
                lines.append((line, raw.strip()))
    
    # Check that we have exactly one
    if len(lines) == 0:
        raise RuntimeError('Could not find VERSION in ' + filename)
    if len(lines) > 1:
        raise RuntimeError('Found multiple VERSION\'s in ' + filename)
    line, raw = lines[0]
    
    # Parse the version
    raw = raw[1:].split('   ')[0].strip()  # skip after more than three spaces
    raw = raw.replace('  ', ' ')  # trip double-spaces to one
    version = [int(i) for i in raw.split(' ')]
    
    return tuple(version), line


def main():
    """ Print version tuples of SPEC, docs, and all implementations,
    and raise an error if there is a mismatch.
    """
    
    files = collect_files()
    ref_version, line = get_version(files[0])
    fail = []
    
    for filename in files:
        fname = os.path.basename(filename)
        version, line = get_version(filename)
        print(fname.rjust(15) + ':', str(version).ljust(10), repr(line[:50]))
        if version[:2] != ref_version:
            fail.append(fname)
    
    if fail:
        raise RuntimeError('Version %s mismatch for %s.' % (version, fail))
    else:
        print('Versions look ok!')


if __name__ == '__main__':
    main()
