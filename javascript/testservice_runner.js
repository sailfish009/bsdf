/* This little script gets called in a subprocess by the BSDF test service */

fs = require('fs');
var bsdf = require('./bsdf.js');
var assert = console.assert;

// argv 0 and 1 are node and the name of the script
fname1 = process.argv[2];
fname2 = process.argv[3];

// Read data
if (fname1.endsWith('.json')) {
	text = fs.readFileSync(fname1, 'utf-8');
	data = JSON.parse(text);
} else if (fname1.endsWith('.bsdf')) {
	bb = fs.readFileSync(fname1, {encoding: null});
	data = bsdf.decode(bb);
} else {
	throw "Unexpected file extension for " + fname1;
}

// Write back (the wrapping into a buffer is needed on Node 4.2)
if (fname2.endsWith('.json')) {
	text = JSON.stringify(data);
	fs.writeFileSync(fname2, text, 'utf-8');
} else if (fname2.endsWith('.bsdf')) {
	bb = bsdf.encode(data);
	fs.writeFileSync(fname2, new Buffer(bb), {encoding: null});
} else {
	throw "Unexpected file extension for " + fname2;
}
