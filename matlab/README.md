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
>> bsdf = Bsdf()
>> b = bsdf.encode({'just some objects', struct('foo', true, 'bar', []), 42.001});
>> size(b)
ans =
   48    1
>> bsdf.decode(b)
ans =
{
  [1,1] = just some objects
  [1,2] =

    scalar structure containing the fields:

      foo = 1
      bar = [](0x0)

  [1,3] =  42.001
}
```


## Reference:
    

## Class Bsdf<span class='sig'>()</span>

This class represents the main API to use BSDF in Matlab.

Options (for writing) are provided as object properties:
    
* compression: the compression for binary blobs, 0 for raw, 1 for zlib
  (not available in Octave).
* float64: whether to export floats as 64 bit (default) or 32 bit.
* use_checksum: whether to write checksums for binary blobs, not yet
  implemented.


### Method save<span class='sig'>(filename, data)</span>

Save data to a file.


### Method load<span class='sig'>(filename)</span>

Load data from a file.


### Method encode<span class='sig'>(data)</span>

Serialize data to bytes. Returns a blob of bytes (a uint8 array).


### Method decode<span class='sig'>(blob)</span>

Load data from bytes.
