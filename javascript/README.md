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

## Reference:


## Function ``encode(data, extensions)``

Encode the data, using the provided extensions (or the standard extensions
if not given). Returns an `ArrayBuffer` representing the encoded data.
See `BsdfSerializer.encode()` for details.


## Function ``decode(blob, extensions)``

Decode the blob, using the provided extensions (or the standard extensions
if not given). Returns the decoded data.
See `BsdfSerializer.decode()` for details.


## Class ``BsdfSerializer(extensions)``

Provides a BSDF serializer object with a particular set of extension.


### Method ``add_extension(extension)``

Add an extension object to the the serializer.


### Method ``remove_extension(extension)``

Remove an extension instance (and any extension with the same name).


### Method ``encode(data)``

Encode the data and returns an `ArrayBuffer` representing the encoded data.

Any `ArrayBuffer` and `DataView` objects present in the data are interpreted
as byte blobs, while `Uint8Array` objects are interpreted as typed arrays.


### Method ``decode(blob)``

Decode the blob and returns the decoded data.

Any encoded byte blobs are will be represented using `DataView` objects that
provide a view (not a copy) on the input data. These can be mapped to an array
with e.g. `a = new Uint8Array(bytes.buffer, bytes.byteOffset, bytes.byteLength)`.
If needed, a copy can be made with `a = new Uint8Array(a)`.

## Extensions

Extensions are represented by objects that have the following attributes:

* a string `name` indicating the identifier of the extension.
* a function `match(s, v)` that is called with a serializer object and a value,
  and should return `true` if the extension should be used.
* a function `encode(s, v)` that converts a value to more primitive objects.
* a function `decode(s, v)` that converts primitive objects into the intended form.
