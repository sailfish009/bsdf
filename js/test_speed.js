/* Test BSDF performance in node.js
 */

//<script src='../data/data03.js'></script>
bsdf = require('./bsdf.js');
bsdf_encode = bsdf.bsdf_encode;
bsdf_decode = bsdf.bsdf_decode;

rand01 = require('../data/rand01.json');
rand02 = require('../data/rand02.json');
rand03 = require('../data/rand03.json');
rand04_nulldict = require('../data/rand04_nulldict.json');
rand05_nulllist = require('../data/rand05_nulllist.json');


// ========== functions we need here

function perf_counter() {
    var t = process.hrtime();
    return t[0] + t[1]*1e-9;
}

function write(msg) {
    if (msg === undefined) msg = '';
    console.log(msg)
}

// ========== Function we can share

function deep_compare(d1, d2) {
    var s1 = JSON.stringify(d1);
    var s2 = JSON.stringify(d2);
    for (var i=0; i<Math.max(s1.length, s2.length); i++) {
          if (s1[i] != s2[i]) {
              var i0 = Math.max(0, i - 10);
              write('Dicts are NOT equal:')
              write(s1.slice(i0, i0 + 100));
              write(s2.slice(i0, i0 + 100));
              return;
          }
    }
    write('Hooray, dicts are equal!')
}

function main() {
    var tests = [['rand01', 100],
                 ['rand02', 10],
                 ['rand03', 1],
                 ['rand04_nulldict', 2],
                 ['rand05_nulllist', 4],
                 ];

    for (var iter=0; iter<tests.length; iter++) {
        var fname = tests[iter][0];
        var n = tests[iter][1];
        write(); write();
        write('=== ' + fname + ' ' + n);

        var d = eval(fname);

        t0 = perf_counter();
        for (var i=0; i<n; i++) { r1 = JSON.stringify(d); }
        t1 = perf_counter() - t0;

        t0 = perf_counter();
        for (var i=0; i<n; i++) { r2 = bsdf_encode(d); }
        t2 = perf_counter() - t0;

        r = Math.round;
        write('encoding: ' + r(t1) + ', ' + r(t2) + ': ' + r(100 * t1/t2) + '%')

        t0 = perf_counter();
        for (var i=0; i<n; i++) { d1 = JSON.parse(r1); }
        t1 = perf_counter() - t0;

        t0 = perf_counter();
        for (var i=0; i<n; i++) { d2 = bsdf_decode(r2); }
        t2 = perf_counter() - t0;

        write('decoding: ' + r(t1) + ', ' + r(t2) + ': ' + r(100 * t1/t2) + '%')

        deep_compare(d1, d2);
    }
}


// ========== start
main()
