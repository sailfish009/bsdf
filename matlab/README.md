# BSDF Matlab/Octave implementation

This is the implementation of the BSDF format for Matlab/Octave. It's
in good shape and well tested. Though it could do with some love from 
a Matlab expert to optimize the code and/or improve the implementation,
e.g. by allowing custom extensions.


## Installation

Download [Bsdf.m](Bsdf.m) and place it in a directory where Matlab can find it,
e.g. by doing:

```matlab
addpath('/path/to/bsdf');
```


## Usage

Functionality is provided via a single `Bsdf` class:

```matlab
bsdf = Bsdf()
bsdf.save(filename, data)   % to save data to file
data = bsdf.load(filename)  % to load data from file
blob = bsdf.encode(data)    % to serialize data to bytes (a uint8 array)
data = bsdf.decode(blob)    % to load data from bytes       
```

Options (for writing) are provided as object properties:
    
* compression: the compression for binary blobs, 0 for raw, 1 for zlib
  (not available in Octave).
* float64: whether to export floats as 64 bit (default) or 32 bit.
* use_checksum: whether to write checksums for binary blobs, not yet
  implemented.
