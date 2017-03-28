/* Test BSDF performance in node.js
 */

//<script src='../data/data03.js'></script>
bsdf = require('./bsdf.js')
test_data = require('../data/data03.js')

console.log(bsdf)
bsdf_encode = bsdf.bsdf_encode;
bsdf_decode = bsdf.bsdf_decode;

function deep_compare(d1, d2) {
    var s1 = JSON.stringify(d1);
    var s2 = JSON.stringify(d2);
    for (var i=0; i<Math.max(s1.length, s2.length); i++) {
          if (s1[i] != s2[i]) {
              var i0 = Math.max(0, i - 10);
              console.log('Dicts are NOT equal:')
              console.log(s1.slice(i0, i0 + 100));
              console.log(s2.slice(i0, i0 + 100));
              return;
          }
    }
    console.log('Hooray, dicts are equal!')
}

function perf_counter() {var t = process.hrtime(); return t[0] + t[1]*1e-9;}

d = testdata;
console.log('parsed test data. starting tests...')

//var t0, t1, t2, r1, r2, d1, d2;

t0 = perf_counter();
r1 = JSON.stringify(d);
t1 = 1000 * (perf_counter() - t0);

t0 = perf_counter();
r2 = bsdf_encode(d);
t2 = 1000 * (perf_counter() - t0);

r = Math.round;
console.log('encoding: ' + r(t1) + ', ' + r(t2) + ': ' + r(100 * t1/t2) + '%');


t0 = perf_counter();
d1 = JSON.parse(r1);
t1 = 1000 * (perf_counter() - t0);

t0 = perf_counter();
d2 = bsdf_decode(r2);
t2 = 1000 * (perf_counter() - t0);

console.log('decoding: ' + r(t1) + ', ' + r(t2) + ': ' + r(100 * t1/t2) + '%');

deep_compare(d1, d2);


