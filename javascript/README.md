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

Note that `ArrayBuffer` and `DataView` are consumed as bytes, while
`Uint8Array` as a typed array.
