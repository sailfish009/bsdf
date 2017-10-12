/* Unit tests for BSDF JavaScript implementations. Note that most things are covered by the test service.
 */

// Imports and definitions
var bsdf = require('./bsdf.js');
var assert = console.assert;
function str (ob) {return JSON.stringify(ob); }


/* Test real basiscs: ints
 */
a = [-3000, -200, -1, 2, 300, 4000];
b = bsdf.encode(a);
c = bsdf.decode(b);

assert(str(a) == str(c), a, c);


/* Test real basiscs: floats
 */
a = [-99.1, 0.0, 0.00012, 980981.12];
b = bsdf.encode(a);
c = bsdf.decode(b);

assert(str(a) == str(c), a, c);


/* Test real basics: bytes
 */
a = new Uint8Array([4, 5, 6]);
b = bsdf.encode(a.buffer);
c = bsdf.decode(b);

assert(a.buffer instanceof ArrayBuffer, a);
// todo: assert(b.buffer instanceof ArrayBuffer, b);
// todo: assert(c.buffer instanceof ArrayBuffer, c);
d = new Uint8Array(c);

for (i=0; i<3; i++) {
    assert(a[0] == d[0], a, d);
}




/* Test integer encoding.
 * This test encodes and decodes int32 numbers via two approaches.
 * We use int32 here because we can actually test the result. In BSDF
 * this same algorithm is applied to implement int64.
 * We test it on numbers that include byte boundaries.
 */

buf = new ArrayBuffer(8);
bufi32 = new Int32Array(buf);
bufu16 = new Uint16Array(buf);
bufu8 = new Uint8Array(buf);

aa = [0, -1, -2, 1, 2, 42, -1337,
      -126, -127, -128, -129, -254, -255, -256, -257,
      126,  127,  128,  129,  254,  255,  256,  257,
      -32766, -32767, -32768, -32769, -65534, -65535, -65536, -65537,
      32766,  32767,  32768,  32769,  65534,  65535,  65536,  65537,
      -2147483647, -2147483648, 2147483646, 2147483647, // these should just work in a int32.
      ];

for (i=0; i<aa.length; i++) {
    a = aa[i];
    
    // encode via uint16
    // I suppose that this would fail on Big Endian systems ...
    if (a < 0) {
        a_ = a + 1;
        bufu16[0] = ((-(a_ % 65536 )) & 65535) ^ 65535;
        bufu16[1] = ((-(a_ / 65536)) & 65535) ^ 65535;
    } else {
        bufu16[0] = (a % 65536 );
        bufu16[1] = (a / 65536 ) & 65535;
    }
    
    // decode via uint16
    //var isneg = (bufu8[3] & 0x80) > 0;
    var isneg = (bufu16[1] & 0x8000) > 0;
    if (isneg) {
        b = -1 - (bufu16[0] ^ 65535) - (bufu16[1] ^ 65535) * 65536;
    } else {
        b = bufu16[0] + bufu16[1] * 65536;
    }
    
    assert(a == bufi32[0], a, bufi32[0]);
    assert(a == b, a, b);
    console.log(a, b, isneg, 'ok');
}

for (i=0; i<aa.length; i++) {
    a = aa[i];

    // encode via uint8 (inspired by msgpack)
    if (a < 0) {
        a_ = a + 1;
        for (j=0; j<4; j++) {
            bufu8[j] = ((-(a_ % 256 )) & 255) ^ 255;
            a_ /= 256;
        }
    } else {
        a_ = a;
        for (j=0; j<4; j++) {
            bufu8[j] = ((a_ % 256 ) & 255);
            a_ /= 256;
        }
    }

    // decode via uint8 (inspired by msgpack)
    var isneg = (bufu8[3] & 0x80) > 0;
    if (isneg) {
        b = -1;
        m = 1;
        for (j=0; j<4; j++) {
            b -= (bufu8[j] ^ 0xff) * m;
            m *= 256;
        }
    } else {
        b = 0;
        m = 1;
        for (j=0; j<4; j++) {
            b += bufu8[j] * m;
            m *= 256;
        }
    }

    assert(a == bufi32[0], a, bufi32[0]);
    assert(a == b, a, b);
    console.log(a, b, isneg, 'ok');
}


//----
console.log('all tests passed');
