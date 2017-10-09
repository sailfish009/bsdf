# BSDF Matlab/Octave implementation

This is the implementation of the BSDF format for Matlab/Octave. It's
in good shape and well tested. Though it could do with some love from 
a Matlab expert to optimize the code and/or improve the implementation,
e.g. by allowing custom converters.


## Installation

Download [bsdf.m](bsdf.m) and place it in a directory where Matlab can find it,
e.g. by doing:

```matlab
addpath('/path/to/bsdf');
```

## Development

Run `invoke -l` in this directory for available tasks (like tests).


## Usage

Functionality is provided via a single `bsdf` function:

<pre style='font-size:80%;'>
data = bsdf(filename)  % to load data from file
data = bsdf(bytes)     % to load data from bytes
bsdf(filename, data)   % to save data to file
bytes = bsdf(data)     % to serialize data to bytes (a uint8 array)
</pre>

Options (for writing) can be provided via argument pairs:
    
* compression: the compression for binary blobs, 0 for raw, 1 for zlib
  (not available in Octave).
* float64: whether to export floats as 64 bit (default) or 32 bit.
* use_checksum: whether to write checksums for binary blobs, not yet
  implemented.
