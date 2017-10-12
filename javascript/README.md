# BSDF Javascript implementation

This implementation of BSDF is intended for use in NodeJS or the browser.
It is a "lite" implementation, without support for e.g. lazy loading
or streaming.

## Installation

Include [bsdf.js](bsdf.js) in your project.


## Reference

```
bsdf = require('bsdf.js');

var bb = bsdf.encode(data1);

data2 = bsdf.decode(bb);
```
