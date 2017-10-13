# BSDF Javascript implementation

This implementation of BSDF is intended for use in NodeJS or the browser.
It is a "lite" implementation, without support for e.g. lazy loading
or streaming.

## Installation

Include [bsdf.js](bsdf.js) in your project.


## Reference

```
bsdf = require('bsdf.js');

var bytes = bsdf.encode(data1);  # produces an ArrayBuffer

data2 = bsdf.decode(bytes);  # bytes can be ArrayBuffer, DataView or Uint8Array.
```

ArrayBuffer and DataView are consumed as bytes, and Uint8Array as a typed array.
Bytes are decoded as DataView objects, which can be mapped to arrays with e.g.
`a = new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength)`, if needed
make a copy with `a = new Uint8Array(a)`.
 