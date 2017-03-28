"""
A modified version of the ZON format (currently in pyzolib/zon) that
is somewhat more pretty and easier/faster to parse. I might want to use this
someday. Can be nice for ini-like files.
"""

import re
import sys


# todo: turn ' = ' into ': '

ESCAPE = re.compile(r"[\x00-\x1f\\'\b\f\n\r\t]")
ESCAPE_DCT = {
    '\\': '\\\\',
    "'": "\\'",
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
# for i in range(0x20):
    # ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))

ESCAPE_DCT2 = {}
for k, v in ESCAPE_DCT.items():
    ESCAPE_DCT2[v] = k
ESCAPE_TABLE = str.maketrans(ESCAPE_DCT)

def py_encode_basestring(s):
    """Return a JSON representation of a Python string

    """
    return '"' + ESCAPE.sub(lambda match: ESCAPE_DCT[match.group(0)], s) + '"'

# todo: needs work on legacy py
_str_encode = lambda s: s.translate(ESCAPE_TABLE)


def make_encoder():
    
    # From six.py
    if sys.version_info[0] >= 3:
        string_types = str
        integer_types = int
        small_types = type(None), bool, int, float, str
        _intstr = int.__str__
    else:
        string_types = basestring  # noqa
        integer_types = (int, long)  # noqa
        small_types = type(None), bool, int, long, float, basestring
        _intstr = lambda i: str(i).rstrip('L')
    
    _floatstr = float.__repr__
    
    # todo: smart mode, comnpact mode and expanded mode
    def pretty(key, islist, indent, iter):
        parts = list(iter)
        if not parts or (len(parts[0]) < 80 and sum(len(p) for p in parts) < 80):
            x = ', '.join(parts)
            fmt = '{%s}'
        else:
            ind = ' ' * (indent + 2)
            x = ('\n' + ind).join(parts)
            fmt = '{\n' + ind + '%s\n' + ind[:-2] + '}'
        if islist:
            fmt = fmt.replace('{', '[').replace('}', ']')
        if key:
            fmt = key + ' = ' + fmt
        return fmt % x
    
    def encode_dict(val, indent):
        
        for key, value in val.items():
            assert key.isidentifier()
            #yield ' ' * indent + key
            
            if value is None:
                yield key + ' = null'
            elif value is True:
                yield key + ' = true'
            elif value is False:
                yield key + ' = false'
            elif isinstance(value, integer_types):
                yield '%s = %s' % (key, _intstr(value))
            elif isinstance(value, float):
                yield '%s = %s' % (key, _floatstr(value))
            elif isinstance(value, string_types):
                yield "%s = '%s'" % (key, _str_encode(value))
            elif isinstance(value, dict):
                yield pretty(key, 0, indent, encode_dict(value, indent + 2))
            elif isinstance(value, (list, tuple)):
                yield pretty(key, 1, indent, encode_list(value, indent + 2))
            else:
                # We do not know            
                data = 'Null'
                tmp = repr(value)
                if len(tmp) > 64:
                    tmp = tmp[:64] + '...'
                if name is not None:
                    print("ZON: %s is unknown object: %s" %  (name, tmp))
                else:
                    print("ZON: unknown object: %s" % tmp)
    
    def encode_list(val, indent):
        
        for value in val:
            
            if value is None:
                yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, integer_types):
                yield _intstr(value)
            elif isinstance(value, float):
                yield _floatstr(value)
            elif isinstance(value, string_types):
                yield "'%s'" % _str_encode(value)
            elif isinstance(value, dict):
                yield pretty(None, 0, indent, encode_dict(value, indent + 2))
            elif isinstance(value, (list, tuple)):
                yield pretty(None, 1, indent, encode_list(value, indent + 2))
            else:
                # We do not know            
                data = 'Null'
                tmp = repr(value)
                if len(tmp) > 64:
                    tmp = tmp[:64] + '...'
                if name is not None:
                    print("ZON: %s is unknown object: %s" %  (name, tmp))
                else:
                    print("ZON: unknown object: %s" % tmp)
    
    return encode_dict


encode = make_encoder()

def saves(d):
    return '{' + '\n'.join(encode(d, 0)) + '}'


dumps = saves  # json compat



## Decoder

import re

def make_decoder():
        
    NaN = float('nan')
    PosInf = float('inf')
    NegInf = float('-inf')
    
    FLAGS = re.UNICODE | re.MULTILINE
    
    item_finder = re.compile(
        '(?:(\{?\s*\,?\s*\})|' +                # end of dict: gr 0
        '(?:(?:\{)|(?:\s*\,)|(?:\s*$))' +       # separator (start of dict, comma or newline)
        '\s*((?![0-9])[_\w]+)\s*=' +            # name: gr 1
        '\s*(?:' +
        '([\+|\-]?[0-9]+\.[\.e\+\-0-9]*)|' +    # float: gr 2
        '([\+|\-]?[0-9]+)|' +                   # int: gr 3
        '([a-z]+)|' +	                        # identifier (nan, inf etc.): gr 4
    r'((?:"(?:|.*?[^\\])(?:\\\\)*")|' +     	# str: gr 5
    r"(?:'(?:|.*?[^\\])(?:\\\\)*'))|" +     	# (part of the above group)
        '(\[|\{)'                               # opening parenthesis (gr 6)
        '))', FLAGS)
    
    value_finder = re.compile(
        '(?:(\[?\s*\,?\s*\])|' +                # end of list: gr 0
        '(?:(?:\[)|(?:\s*\,)|(?:\s*$))' +       # separator (start of list, comma or newline)
        '\s*(?:' +                                # (also a group, so that groups indices are the same)
        '([\+|\-]?[0-9]+\.[\.e\+\-0-9]*)|' +    # float: gr 2
        '([\+|\-]?[0-9]+)|' +                   # int: gr 3
        '([a-z]+)|' +	                        # identifier (nan, inf etc.): gr 4
    r'((?:"(?:|.*?[^\\])(?:\\\\)*")|' +     	# str: gr 5
    r"(?:'(?:|.*?[^\\])(?:\\\\)*'))|" +     	# (part of the above group)
        '(\[|\{)'                               # opening parenthesis (gr 6)
        '))', FLAGS)
    
    # value_finder = re.compile(
    #     '(?:(\[?\s*\,?\s*\])|' +                # end of list: gr 0
    #     '(?:(?:\[)|(?:\s*\,)|(?:\s*$))' +       # separator (start of list, comma or newline)
    #     '\s*(' +                                # (also a group, so that groups indices are the same)
    #     '(?:[\+|\-]?[0-9]+\.[\.e\+\-0-9]*)|' +    # float: gr 2
    #     '(?:[\+|\-]?[0-9]+)|' +                   # int: gr 3
    #     '(?:[a-z]+)|' +	                        # identifier (nan, inf etc.): gr 4
    #    r'(?:(?:"(?:|.*?[^\\])(?:\\\\)*")|' +     	# str: gr 5
    #    r"(?:'(?:|.*?[^\\])(?:\\\\)*'))|" +     	# (part of the above group)
    #     '(?:\[|\{)'                               # opening parenthesis (gr 6)
    #     '))', FLAGS)
    
    str_decoder = re.compile('(%s)' % '|'.join(re.escape(x) for x in ESCAPE_DCT.values()))
    
    def parse_dict(text, pos):
        
        d = {}
        first = True
        
        while True:
            
            # Match sep or end
            match = item_finder.match(text, pos)
            if not match:
                if pos == len(text):
                    return d, pos
                else:
                    raise RuntimeError('Expected new item or dict end')
            
            pos = match.end()
            groups = match.groups()
            
            if groups[0]:  # closing bracket
                return d, pos
            
            name = groups[1]
            
            if groups[2]:
                d[name] = float(groups[2])
            elif groups[3]:
                d[name] = int(groups[3])
            elif groups[4]:
                token = groups[4].lower()
                if token == 'null':
                    d[name] = None
                elif token == 'false':
                    d[name] = False
                elif token == 'true':
                    d[name] = True
                elif token == 'nan':
                    d[name] = NaN
                elif token.endswith('inf'):
                    d[name] = float(token)
                else:
                    raise RuntimeError('Unknown value %r' % token)
            elif groups[5]:
                value = groups[5]
                d[name] = str_decoder.sub(lambda k: ESCAPE_DCT2[value[k.start():k.end()]], value)
            elif groups[6]:
                if groups[6] == '[':
                    d[name], pos = parse_list(text, pos-1)
                else:  # '{'
                    d[name], pos = parse_dict(text, pos-1)
            else:
                assert False  # we should not ever get here
    
    
    def parse_list(text, pos):
        
        values = []
        first = True
        
        while True:
            
            # Match sep or end
            match = value_finder.match(text, pos)
            if not match:
                if pos == len(text):
                    return values, pos
                else:
                    raise RuntimeError('Expected new value list end')
            
            pos = match.end()
            groups = match.groups()
            
            if groups[0]:  # closing bracket
                return values, pos
            
            if groups[1]:
                values.append(float(groups[1]))
            elif groups[2]:
                values.append(int(groups[2]))
            elif groups[3]:
                token = groups[3].lower()
                if token == 'null':
                    values.append(None)
                elif token == 'false':
                    values.append(False)
                elif token == 'true':
                    values.append(True)
                elif token == 'nan':
                    values.append(NaN)
                elif token.endswith('inf'):
                    values.append(float(token))
                else:
                    raise RuntimeError('Unknown value %r' % token)
            elif groups[4]:
                value = groups[4]
                values.append(str_decoder.sub(lambda k: ESCAPE_DCT2[value[k.start():k.end()]], value))
            elif groups[5]:
                if groups[5] == '[':
                    value, pos = parse_list(text, pos-1)
                    values.append(value)
                else:  # '{'
                    value, pos = parse_dict(text, pos-1)
                    values.append(value)
            else:
                assert False  # we should not ever get here
            
            # token = groups[1]
            # 
            # if token.isidentifier():
            #     token = token.lower()
            #     if token == 'null':
            #         values.append(None)
            #     elif token == 'false':
            #         values.append(False)
            #     elif token == 'true':
            #         values.append(True)
            #     elif token == 'nan':
            #         values.append(NaN)
            #     elif token.endswith('inf'):
            #         values.append(float(token))
            #     else:
            #         raise RuntimeError('Unknown value %r' % token)
            # elif token[0] in '"\'':
            #     value = token
            #     values.append(str_decoder.sub(lambda k: ESCAPE_DCT2[value[k.start():k.end()]], value))
            # elif token == '[':
            #     value, pos = parse_list(text, pos-1)
            #     values.append(value)
            # elif token == '{':
            #     value, pos = parse_dict(text, pos-1)
            #     values.append(value)
            # elif token.isnumeric():
            #     values.append(int(token))
            # else:
            #     try:
            #         values.append(float(token))
            #     except Exception:
            #         raise RuntimeError('Wrong value')
    return parse_dict

decoder = make_decoder()

def loads(text):
    return decoder(text, 0)[0]
    #return parse_dict(tokenizer(text))

# loads('foo = "a\nb"\nbla =3 ')


