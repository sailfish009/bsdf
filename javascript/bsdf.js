
/* JavaScript implementation of the Binary Structured Data Format (BSDF)
 *
 * See http://gitlab.com/almarklein/bsdf for more information.
 *
 */

/* Developer notes:
 *
 * To represent bytes we need to chose between Uint8Array and ArrayBuffer. The latter
 * most closely resembles abstract byte blobs, but it cannot be a view. We consider
 * ArrayBuffer byte blobs, but the encode() and decode() function produce/accept Uint8Array.
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define("bsdf", [], factory);
    } else if (typeof exports !== 'undefined') {
        // Node or CommonJS
        module.exports = factory();
        if (typeof window === 'undefined') {
            root.bsdf = module.exports;  // also create global module in Node
        }
    } else {
        // Browser globals (root is window)
        root.bsdf = factory();
    }
}(this, function () {
/* above is the UMD module prefix */

"use strict";

var VERSION = [2, 0, 0];

// http://github.com/msgpack/msgpack-javascript/blob/master/msgpack.js#L181-L192
function utf8encode(mix) {
    // Mix is assumed to be a string. returns an Array of ints.
    var iz = mix.length;
    var rv = [];
    for (var i = 0; i < iz; ++i) {
        var c = mix.charCodeAt(i);
        if (c < 0x80) { // ASCII(0x00 ~ 0x7f)
            rv.push(c & 0x7f);
        } else if (c < 0x0800) {
            rv.push(((c >>>  6) & 0x1f) | 0xc0, (c & 0x3f) | 0x80);
        } else if (c < 0x10000) {
            rv.push(((c >>> 12) & 0x0f) | 0xe0,
                    ((c >>>  6) & 0x3f) | 0x80, (c & 0x3f) | 0x80);
        }
    }
    return rv;
}

// http://github.com/msgpack/msgpack-javascript/blob/master/msgpack.js#L365-L375
function utf8decode(buf) {
    // The buf is assumed to be an Array or Uint8Array. Returns a string.
    var iz = buf.length - 1;
    var ary = [];
    for (var i = -1; i < iz; ) {
        var c = buf[++i]; // lead byte
        ary.push(c < 0x80 ? c : // ASCII(0x00 ~ 0x7f)
                c < 0xe0 ? ((c & 0x1f) <<  6 | (buf[++i] & 0x3f)) :
                            ((c & 0x0f) << 12 | (buf[++i] & 0x3f) << 6
                                            | (buf[++i] & 0x3f)));
    }
    return String.fromCharCode.apply(null, ary);
}


//---- encoder

function ByteBuilder() {
    // We use an arraybuffer for efficiency, but we don't know its final size.
    // Therefore we create a new one with increasing size when needed.
    var buffers = [];
    var buf = new ArrayBuffer(8);
    var buf8 = new Uint8Array(buf);
    //var buf64 = new Uint64Array(buf);
    var bufdv = new DataView(buf);
    var pos = 0;

    // Create text encoder / decoder
    var text_encode, text_decode;
    if (typeof TextEncoder !== 'undefined') {
        var x = new TextEncoder('utf-8');
        text_encode = x.encode.bind(x);
    } else {
        // test this
        text_encode = utf8encode;
    }

    function get_bytes() {
        return new Uint8Array(buf, 0, pos);
    }
    function need_size(n) {
        // establish size
        var new_size = buf.byteLength;
        while (new_size < n) { new_size += Math.min(new_size, 65536); }
        // create new (larger) copy of buffer
        var old8 = buf8;
        // buf = ArrayBuffer.transfer(buf, new_size); --> not yet supported
        buf = new ArrayBuffer(new_size);
        buf8 = new Uint8Array(buf);
        //buf64 = new Uint64Array(buf);
        bufdv = new DataView(buf);
        for (var i=0; i<old8.length; i++) {buf8[i] = old8[i]; }
    }
    function tell() {
        return pos;
    }
    function push_bytes(s) { // uint8Array
        var n = s.byteLength;
        if (pos + n > buf.byteLength) { need_size(pos + n); }
        for (var i=0; i<n; i++) { buf8[pos+i] = s[i]; }
        pos += n;
    }
    function push_char(s) {
        if (pos + 1 > buf.byteLength) { need_size(pos + 1); }
        buf8[pos] = s.charCodeAt();
        pos += 1;
    }
    function push_str(s) {
        var bb = text_encode(s);
        push_size(bb.length);
        if (pos + bb.length > buf.byteLength) { need_size(pos + bb.length); }
        for (var i=0; i<bb.length; i++) { buf8[pos + i] = bb[i]; }
        pos += bb.length;
    }
    function push_size(s, big) {
        if (s <= 250 && typeof big == 'undefined') {
            if (pos + 1 > buf.byteLength) { need_size(pos + 1); }
            buf8[pos] = s;
            pos += 1;
        } else {
            if (pos + 9 > buf.byteLength) { need_size(pos + 9); }
            buf8[pos] = 253;
            bufdv.setUint32(pos+1, (s % 4294967296), true); // uint64
            bufdv.setUint32(pos+5, (s / 4294967296) & 4294967295, true);
            pos += 9;
        }
    }
    function push_uint8(s) {
        if (pos + 1 > buf.byteLength) { need_size(pos + 1); }
        buf8[pos] = s;
        pos += 1;
    }
    function push_int(s) {
        if (pos + 8 > buf.byteLength) { need_size(pos + 8); }
        if (s < 0) { // perform two's complement encoding
            for (var j=0, a=s+1; j<8; j++, a/=256) { buf8[pos+j] = ((-(a % 256 )) & 255) ^ 255; }
        } else {
            for (var j=0, a=s; j<8; j++, a/=256) { buf8[pos+j] = ((a % 256 ) & 255); }
        }
        pos += 8;
    }
    function push_float64(s) {
        // todo: we could push 32bit floats via "f"
        if (pos + 8 > buf.byteLength) { need_size(pos + 8); }
        bufdv.setFloat64(pos, s, true);
        pos += 8;
    }
    return {get_bytes: get_bytes, tell: tell, push_bytes: push_bytes,
            push_char: push_char, push_str: push_str, push_size: push_size,
            push_uint8: push_uint8, push_int: push_int, push_float64: push_float64}
}

function encode_type_id(f, c, converter_id) {
    if (typeof converter_id == 'undefined') {
        f.push_char(c);
    } else {
        f.push_char(c.toUpperCase());
        f.push_str(converter_id);
    }
}

function encode_object(f, value, converter_id) {

    if (value === null) { encode_type_id(f, 'v', converter_id); }
    //else if (typeof value == 'undefined') { encode_type_id(f, 'v', converter_id); }
    else if (value === false) { encode_type_id(f, 'n', converter_id); }
    else if (value === true) { encode_type_id(f, 'y', converter_id); }
    else if (typeof value == 'number') {
        if (Number.isInteger(value)) {
            if (value >= 0 && value <= 255) {
                encode_type_id(f, 'u', converter_id);
                f.push_uint8(value);
            } else {
                encode_type_id(f, 'i', converter_id);
                f.push_int(value);
            }
        } else {
            encode_type_id(f, 'd', converter_id);
            f.push_float64(value);
        }
    } else if (typeof value == 'string') {
        encode_type_id(f, 's', converter_id);
        f.push_str(value);
    } else if (typeof value == 'object') {
        if (Array.isArray(value)) {  // heterogeneous list
            encode_type_id(f, 'l', converter_id);
            var n = value.length;
            f.push_size(n);
            for (var i=0; i<n; i++) {
                encode_object(f, value[i]);
            }
        } else if (value.constructor === Object) {  // mapping / dict
            encode_type_id(f, 'm', converter_id);
            var n = Object.keys(value).length;
            f.push_size(n);
            for (var key in value) {
                f.push_str(key);
                encode_object(f, value[key]);
            }
        } else if (value instanceof ArrayBuffer) {  // bytes
            encode_type_id(f, 'b', converter_id);
            var compression = 0;
            var compressed = new Uint8Array(value);
            var data_size = value.byteLength;
            var used_size = data_size;
            var extra_size = 0;
            var allocated_size = used_size + extra_size;
            // Write sizes - write at least in a size that allows resizing
            if (allocated_size > 250) {  // && compression == 0
                f.push_size(allocated_size, true);
                f.push_size(used_size, true);
                f.push_size(data_size, true);
            } else {
                f.push_size(allocated_size);
                f.push_size(used_size);
                f.push_size(data_size);
            }
            // Compression and checksum
            f.push_uint8(0);
            f.push_uint8(0);  // no checksum
            // Byte alignment
            if (compression == 0) {
                var alignment = (f.tell() + 1) % 8  // +1 for the byte to write
                f.push_uint8(alignment);
                for (var i=0; i<alignment; i++) { f.push_uint8(0); }
            } else {
                f.push_uint8(0);  // zero alignment
            }
            // The actual data and extra space
            f.push_bytes(compressed);
            f.push_bytes(new Uint8Array(allocated_size - used_size));
        } else {
            // todo: try converters

            if (value instanceof Complex) {
                encode_object(f, [value.real, value.imag], 'c');
            } else {
                throw "cannot encode object " + value.constructor.name;
            }
        }
    } else {
        throw "cannot encode type " + typeof(value);
    }
}

//---- decoder

function BytesReader(buf) {

    // We need a typed array (not a raw buffer) so we know the offset in the buffer.
    // If we get an ArrayBuffer (or Node Buffer), we just use a zero offset.
    if (buf.constructor !== Uint8Array) { buf = new Uint8Array(buf); }

    var pos = buf.byteOffset;
    var buf = buf.buffer;
    var buf8 = new Uint8Array(buf);
    var bufdv = new DataView(buf);

    // Create text encoder / decoder
    var text_encode, text_decode;
    if (typeof TextDecoder !== 'undefined') {
        var x = new TextDecoder('utf-8');
        text_decode = x.decode.bind(x);
    } else {
        // test this
        text_decode = utf8decode;
    }

    function tell() {
        return pos;
    }
    function get_char() {
        return String.fromCharCode(buf8[pos++]);
    }
    function get_size() {
        var s = buf8[pos++];
        if (s >= 253) {
            if (s == 253) {
                s = bufdv.getUint32(pos, true) + bufdv.getUint32(pos+4, true) * 4294967296;
            } else if (s == 255) {
                s = -1;  // streaming
            } else {
                throw "Invalid size";
            }
            pos += 8;
        }
        return s;
    }
    function get_bytes(n) {  // Uint8Array
        var s = new Uint8Array(buf, pos, n);
        pos += n;
        return s;
    }
    function get_str() {
        var n = get_size();
        var bb = new Uint8Array(buf, pos, n);
        pos += n;
        return text_decode(bb);
    }
    function get_uint8() {
        return buf8[pos++];
    }
    function get_int() {
        var isneg = (buf8[pos+7] & 0x80) > 0;
        if (isneg) {
            var s = -1;
            for (var j=0, m=1; j<8; j++, m*=256) { s -= (buf8[pos+j] ^ 0xff) * m; }
        } else {
            var s = 0;
            for (var j=0, m=1; j<8; j++, m*=256) { s += buf8[pos+j] * m; }
        }
        pos += 8;
        return s;

    }
    function get_float32() {
        var s = bufdv.getFloat32(pos, true);
        pos += 4;
        return s;
    } function get_float64() {
        var s = bufdv.getFloat64(pos, true);
        pos += 8
        return s;
    }

    return {tell: tell, buf8:buf8, get_size:get_size, get_bytes: get_bytes, get_uint8: get_uint8, get_int: get_int,
            get_float32: get_float32, get_float64: get_float64, get_char: get_char, get_str: get_str};

}

function decode_object(f) {

    var char = f.get_char();
    var c = char.toLowerCase();
    var value;
    var converter_id = null;

    if (char == '\x00') {  // because String.fromCharCode(undefined) produces ASCII 0.
        throw new EOFError('End of BSDF data reached.');
    }

    // Conversion (uppercase value identifiers signify converted values)
    if (char != c) {
        converter_id = f.get_str();
    }

    if (c == 'v') {
        value = null;
    } else if (c == 'n') {
        value = false;
    } else if (c == 'y') {
        value = true;
    } else if (c == 'u') {
        value = f.get_uint8();
    } else if (c == 'i') {
        value = f.get_int();
    } else if (c == 'f') {
        value = f.get_float32();
    } else if (c == 'd') {
        value = f.get_float64();
    } else if (c == 's') {
        value = f.get_str();
    } else if (c == 'l') {
        var n = f.get_size();
        if (n < 0) {
            // Streaming
            value = new Array();
            try {
                while (true) { value.push(decode_object(f)); }
            } catch(err) {
                if (err instanceof EOFError) { /* ok */ } else { throw err; }
            }
        } else {
            // Normal
            value = new Array(n);
            for (var i=0; i<n; i++) {
                value[i] = decode_object(f);
            }
        }
    } else if (c == 'm') {
        var n = f.get_size();
        value = {};
        for (var i=0; i<n; i++) {
            var key = f.get_str();
            value[key] = decode_object(f);
        }
    } else if (c == 'b') {
        // Get sizes
        var allocated_size = f.get_size();
        var used_size = f.get_size();
        var data_size = f.get_size();
        // Compression and checksum
        var compression = f.get_uint8();
        var has_checksum = f.get_uint8();
        if (has_checksum) {
            var checksum = f.get_bytes(16);
        }
        // Skip alignment
        var alignment = f.get_uint8();
        f.get_bytes(alignment)
        // Get data (as ArrayBuffer)
        var compressed = f.get_bytes(used_size);
        f.get_bytes(allocated_size - used_size);  // skip extra space
        if (compression == 0) {
            value = compressed.buffer.slice(compressed.byteOffset, compressed.byteOffset + compressed.byteLength);
        } else {
            throw "JS implementation of BSDF does not support compression (" + compression + ')';
        }
    } else {
        throw "Invalid value specifier at pos " + f.tell() + ": " + JSON.stringify(char);
    }

    // Convert? for now this is hard-coded -> need user-defined converters!
    if (converter_id !== null) {
        if (converter_id == 'c') {
            value = new Complex(value[0], value[1]);
        } else {
            console.log('No known converter for "' + converter_id + '", value passes in raw form.');
        }
    }
    return value;
}


// To be able to support complex numbers
function Complex(real, imag) {
    this.real = real;
    this.imag = imag;
}

function EOFError(msg) {
    this.msg = msg;
}

// ==================


function bsdf_encode(d) {
    var f = ByteBuilder();
    // Write head and version
    f.push_char('B'); f.push_char('S'); f.push_char('D'); f.push_char('F');
    f.push_uint8(VERSION[0]); f.push_uint8(VERSION[1]);
    // Encode and return result
    encode_object(f, d);
    return f.get_bytes();
}

function bsdf_decode(buf) {
    var f = BytesReader(buf);
    // Check head
    var head = f.get_char() + f.get_char() + f.get_char() + f.get_char()
    if (head != 'BSDF') {
        throw "This does not look like BSDF encoded data."
    }
    // Check version
    var major_version = f.get_uint8();
    var minor_version = f.get_uint8();
    if (major_version != VERSION[0]) {
        throw ('Reading file with different major version ' + major_version + ' from the implementation ' + VERSION[0]);
    } else if (minor_version > VERSION[1]){
        console.log('BSDF Warning: reading file with higher minor version ' + minor_version + ' than the implementation ' + VERSION[1]);
    }
    // Decode
    return decode_object(f);
}

// For Node.js
//if (typeof module !== 'undefined') module.exports = {bsdf_encode, bsdf_decode};


/* Below is the UMD module suffix */
exports = {encode: bsdf_encode, decode: bsdf_decode};
return exports;
}));
