# BSDF Javascript implementation

This implementation of BSDF is intended for use in NodeJS or the browser.
It is a "lite" implementation, without support for e.g. lazy loading
or streaming.

## Installation

Include [bsdf.js](bsdf.js) in your project.


## Usage

Basic usage:
```js
var bsdf = require('bsdf.js');
var data1 = ...
var bytes = bsdf.encode(data1);  // produces an ArrayBuffer
var data2 = bsdf.decode(bytes);  // bytes can be ArrayBuffer, DataView or Uint8Array.
```

Full example using extensions:
```js
// A class that we want to encode
function MyOb(val) {
    this.val = val;
}
// The extension that can encode/decode it
var myext = {name: 'test.myob',
             match: function (v) { return v instanceof MyOb; },
             encode: function (v) { return v.val; },
             decode: function (v) { return new MyOb(v); }
             };
// Determine extensions to use (include standard ones)
var extensions = Array.concat(bsdf.standard_extensions, [myext]);
// Encode and decode
var data1 = new MyOb(42);
var bytes = bsdf.encode(data1, extensions);
var data2 = bsdf.decode(bytes);  // -> the raw value, 42
var data3 = bsdf.decode(bytes, extensions);  // a MyOb instance with value 42
```

### A note on encoding of bytes

During encoding, ArrayBuffer or DataView objects are consumed as bytes,
while Uint8Array objects as typed arrays.

During decoding, byte objects are represented as DataView objects, which can
in turn be mapped to arrays with e.g.
`a = new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength)`.
If needed, a copy can be made with `a = new Uint8Array(a)`.
