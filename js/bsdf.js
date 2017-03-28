"use strict"

function base64encode(buf) {
}

function base64decode(buf) {
}

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
        var new_size = buf.byteLength * 2;
        while (new_size < n) { new_size *= 2; }
        // create new (larger) copy of buffer
        var old8 = buf8;
        // buf = ArrayBuffer.transfer(buf, new_size); --> not yet supported
        buf = new ArrayBuffer(new_size);
        buf8 = new Uint8Array(buf);
        //buf64 = new Uint64Array(buf);
        bufdv = new DataView(buf);
        for (var i=0; i<old8.length; i++) {buf8[i] = old8[i]; }
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
        for (var i=0; i<bb.length; i++) {
            buf8[pos + i] = bb[i];
        }
        pos += bb.length;
    }
    function push_size(s) {
        if (s < 255) {
            if (pos + 1 > buf.byteLength) { need_size(pos + 1); }
            buf8[pos] = s;
            pos += 1;
        } else {
            if (pos + 9 > buf.byteLength) { need_size(pos + 9); }
            buf8[pos] = 255;
            bufdv.setFloat64(pos + 1, s, false);  // int encoded as float64
            pos += 9;
        }
    }
    function push_int(s) {
        if (s >= 0 && s <= 255) {
            if (pos + 2 > buf.byteLength) { need_size(pos + 2); }
            buf8[pos] = 'i'.charCodeAt();
            buf8[pos + 1] = s;
            pos += 2;
        } else {
            if (pos + 9 > buf.byteLength) { need_size(pos + 9); }
            buf8[pos] = 'I'.charCodeAt();
            bufdv.setFloat64(pos + 1, s, false);
            pos += 9;
        }
    }
    function push_float(s) {
        // todo: we could push 32bit floats via "f"
        if (pos + 9 > buf.byteLength) { need_size(pos + 9); }
        buf8[pos] = 'F'.charCodeAt();
        bufdv.setFloat64(pos + 1, s, false);
        pos += 9;
    }
    return {get_bytes, get_bytes, push_char: push_char, push_str: push_str,
            push_size: push_size, push_int: push_int, push_float: push_float}
}

function encode_object(f, value) {
    if (value === null) { f.push_char('N') }
    else if (value === false) { f.push_char('n') }
    else if (value === true) { f.push_char('y') }
    else if (typeof value == 'number') {
        if (Number.isInteger(value)) {
            f.push_int(value)
        } else {
            f.push_float(value);
        }
    } else if (typeof value == 'string') {
        f.push_char('s');
        f.push_str(value);
   } else if (typeof value == 'object') {
        if (Array.isArray(value)) {
            f.push_char('L');
            var n = value.length;
            f.push_size(n);
            for (var i=0; i<n; i++) {
                encode_object(f, value[i]);
            }
        } else if (value.constructor === Object) {
            f.push_char('D');
            var n = Object.keys(value).length;
            f.push_size(n);
            for (var key in value) {
                f.push_str(key);
                encode_object(f, value[key]);
            }
        } else {
            throw "cannot encode object " + value.constructor.name;
        }
    } else {
        throw "cannot encode type " + typeof(value);
    }
}

//---- decoder

function BytesReader(buf) {

    // We need a typed array\(not a raw buffer) so we know the offset in the buffer.
    // If we get a buffer, we just use a zero offset.
    if (buf.constructor === ArrayBuffer) { buf = new Uint8Array(buf); }

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

    function get_pos() {
        return pos;
    }
    function get_char() {
        return String.fromCharCode(buf8[pos++]);
    }
    function get_size() {
        var s = buf8[pos++];
        if (s == 255) {
            s = bufdv.getFloat64(pos, false);
            pos += 8;
        }
        return s;
    }
    function get_str() {
        var n = get_size();
        var bb = new Uint8Array(buf, pos, n);
        pos += n;
        return text_decode(bb);
    }
    function get_int(c) {
        if (c == 'i') { return buf8[pos++] }
        else {
            var s = bufdv.getFloat64(pos, false);
            pos += 8;
            return s;
        }
    }
    function get_float(c) {
        if (c == 'f') {
            var s = bufdv.getFloat32(pos, false);
            pos += 4;
            return s;
        } else {
            var s = bufdv.getFloat64(pos, false);
            pos += 8
            return s;
        }
    }

    return {get_pos: get_pos, get_size:get_size, get_int: get_int, get_float: get_float, get_char: get_char, get_str: get_str};

}

function decode_object(f) {

    var c = f.get_char();
    if (c == 'N') { return null; }
    else if (c == 'n') { return false; }
    else if (c == 'y') {return true; }
    else if (c == 'i' || c == 'I') {return f.get_int(c); }
    else if (c == 'f' || c == 'F') {return f.get_float(c); }
    else if (c == 's') { return f.get_str(); }
    else if (c == 'L') {
        /*
        var n = f.get_size();
        var value = new Array(n);
        for (var i=0; i<n; i++) {
            value[i] = decode_object(f);
        }
        return value;
        */
        return decode_list(f);
    }
    else if (c == 'D') {
        /*
        var n = f.get_size();
        var value = {};
        for (var i=0; i<n; i++) {
            var key = f.get_str();
            value[key] = decode_object(f);
        }
        return value;
        */
        return decode_dict(f);
    }
    else { throw "Invalid value specifier at pos " + f.get_pos() + ": " + JSON.stringify(c); }
}

function decode_list(f) {

    var n = f.get_size();
    var value = new Array(n);
    for (var i=0; i<n; i++) {
        var val;

        var c = f.get_char();
        if (c == 'N') { val = null; }
        else if (c == 'n') { val = false; }
        else if (c == 'y') { val = true; }
        else if (c == 'i' || c == 'I') { val = f.get_int(c); }
        else if (c == 'f' || c == 'F') { val = f.get_float(c); }
        else if (c == 's') { val = f.get_str(); }
        else if (c == 'L') { val = decode_list(f); }
        else if (c == 'D') { val = decode_dict(f); }
        else { throw "Invalid value specifier at pos " + f.get_pos() + ": " + JSON.stringify(c); }

        value[i] = val;
    }
    return value;
}

function decode_dict(f) {

    var n = f.get_size();
    var value = {};
    for (var i=0; i<n; i++) {
        var key = f.get_str();
        var val;

        var c = f.get_char();
        if (c == 'N') { val = null; }
        else if (c == 'n') { val = false; }
        else if (c == 'y') { val = true; }
        else if (c == 'i' || c == 'I') { val = f.get_int(c); }
        else if (c == 'f' || c == 'F') { val = f.get_float(c); }
        else if (c == 's') { val = f.get_str(); }
        else if (c == 'L') { val = decode_list(f); }
        else if (c == 'D') { val = decode_dict(f); }
        else { throw "Invalid value specifier at pos " + f.get_pos() + ": " + JSON.stringify(c); }

        value[key] = val;
    }
    return value;
}


// ==================


function bsdf_encode(d) {
    var f = ByteBuilder();
    encode_object(f, d);
    return f.get_bytes();
}

function bsdf_decode(buf) {
    var f = BytesReader(buf);
    return decode_object(f);
}

// For Node.js
module.exports = {bsdf_encode, bsdf_decode};
