"""
A data format that it text-based, but with a binary-like feel;
near-binary but still human readable, kindof. Its actually quite fast
to encode and decode, and human readable is good. But it still
complicates things when having two formats (text-based and binary) in
one file, and the fact that this is not pleasantly-human-readable does
not give it much of an edge.
"""

import re
import sys


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
        if True:#not parts or (len(parts[0]) < 80 and sum(len(p) for p in parts) < 80):
            x = ' '.join(parts)
            fmt = '%s'
        else:
            ind = ' ' * (indent + 2)
            x = ('\n' + ind).join(parts)
            fmt = '\n' + ind + '%s\n' + ind[:-2]
        if islist:
            fmt = 'L' + str(len(parts)) + ' ' + fmt
        else:
            fmt = 'D' + str(len(parts)) + ' ' + fmt
        if key:
            fmt = key + ' ' + fmt
        return fmt % x
    
    def encode_dict(val, indent):
        
        for key, value in val.items():
            assert key.isidentifier()
            #yield ' ' * indent + key
            
            if value is None:
                yield key + ' N'
            elif value is True:
                yield key + ' y'
            elif value is False:
                yield key + ' n'
            elif isinstance(value, integer_types):
                yield '%s i%s' % (key, _intstr(value))
            elif isinstance(value, float):
                yield '%s f%s' % (key, _floatstr(value))
            elif isinstance(value, string_types):
                if value:
                    yield "%s s%i %s" % (key, len(value), value)
                else:
                    yield '%s s0' % key
            elif isinstance(value, dict):
                if value:
                    yield pretty(key, 0, indent, encode_dict(value, indent + 2))
                else:
                    yield '%s D0' % key
            elif isinstance(value, (list, tuple)):
                if value:
                    yield pretty(key, 1, indent, encode_list(value, indent + 2))
                else:
                    yield '%s L0' % key
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
                yield 'N'
            elif value is True:
                yield 'y'
            elif value is False:
                yield 'n'
            elif isinstance(value, integer_types):
                yield 'i' + _intstr(value)
            elif isinstance(value, float):
                yield 'f' + _floatstr(value)
            elif isinstance(value, string_types):
                if value:
                    yield "s%i %s" % (len(value), value)
                else:
                    yield "s0"
            elif isinstance(value, dict):
                if value:
                    yield pretty(None, 0, indent, encode_dict(value, indent + 2))
                else:
                    yield 'D0'
            elif isinstance(value, (list, tuple)):
                if value:
                    yield pretty(None, 1, indent, encode_list(value, indent + 2))
                else:
                    yield 'L0'
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
    return 'D99999999999999 ' + ' '.join(encode(d, 0))


dumps = saves  # json compat

##


def make_decoder():
    #tokenre = re.compile('((\S+)[ \r\t\f\v\n]*)', re.MULTILINE)
    tokenre = re.compile('(([^ \n]+)[ \n]*)', re.MULTILINE)
    #tokenre = re.compile('(?:\r?\n\t*)|(?:\,? +)|(?:\: *)|(?:[ \t\n]*([\}\{\]\[])[ \t\n]*)')
    
    text = ''
    pos = 0
    max_pos = 0
    
    def next():
        nonlocal pos
        match = tokenre.match(text, pos)
        if not match:
            if pos == max_pos:
                return '', ''
            else:
                1/0
        pos = match.end()
        return match.groups()
    
    # def loads(t):
    #     nonlocal text
    #     nonlocal pos
    #     nonlocal max_pos
    #     text = t
    #     pos = re.search('\S', text).start()
    #     max_pos = len(text)
    #     token, _ = next()
    #     assert token.startswith('D99')
    #     return decode_dict(999999999999999)
    
    def loads(t):
        parts = t.split(' ')  # todo: kannie!
        # parts = [part for part in parts if part]
        assert parts[0].startswith('D99')
        return decode_dict(999999999999999, parts, 1)[0]
    
    def decode_dict(nitems, parts, pos):
        items = {}
        while True:
            # todo: why the hell is zon4 so much faster than zon5???
            #for i in range(nitems):
            if len(items) == nitems:
                 return items, pos
            if pos >= len(parts):
                return items, pos
            token2 = parts[pos]
            name = token2
            token2 = parts[pos + 1]
            pos += 2
            if token2[0] == 'N':
                items[name] = None
            elif token2[0] == 'n':
                items[name] = False
            elif token2[0] == 'y':
                items[name] = True
            elif token2[0] == 'i':
                items[name] = int(token2[1:])
            elif token2[0] == 'f':
                items[name] = float(token2[1:])
            elif token2[0] == 's':
                n = int(token2[1:])
                subs = []
                if n:
                    count = 0
                    while count < n:
                        tok = parts[pos] + ' '
                        pos += 1
                        count += len(tok)
                        subs.append(tok)
                    if count > n:
                        subs[-1] = subs[-1][:-(count-n)]
                    if not parts[pos]:
                        pos += 1
                items[name] = ''.join(subs)
            elif token2[0] == 'L':
                n = int(token2[1:])
                items[name], pos = decode_list(n, parts, pos)
            elif token2[0] == 'D':
                n = int(token2[1:])
                items[name], pos = decode_dict(n, parts, pos)
            else:
                raise RuntimeError('Unexpected chars: ' + token2)
        return items, pos
    
    def decode_list(nitems, parts, pos):
        items = []
        for i in range(nitems):
            token2 = parts[pos]
            pos += 1
            if not token2:
                return items, pos
            if token2[0] == 'N':
                items.append(None)
            elif token2[0] == 'n':
                items.append(False)
            elif token2[0] == 'y':
                items.append(True)
            elif token2[0] == 'i':
                items.append(int(token2[1:]))
            elif token2[0] == 'f':
                items.append(float(token2[1:]))
            elif token2[0] == 's':
                n = int(token2[1:])
                subs = []
                if n:
                    count = 0
                    while count < n:
                        tok = parts[pos] + ' '
                        pos += 1
                        count += len(tok)
                        subs.append(tok)
                    if not parts[pos]:
                        pos += 1
                    if count > n:
                        subs[-1] = subs[-1][:-(count-n)]
                items.append(''.join(subs))
            elif token2[0] == 'L':
                n = int(token2[1:])
                v, pos = decode_list(n, parts, pos)
                items.append(v)
            elif token2[0] == 'D':
                n = int(token2[1:])
                v, pos = decode_dict(n, parts, pos)
                items.append(v)
            else:
                raise RuntimeError('Unexpected chars: ' + token2)
        return items, pos
    
    # def decode_dict(nitems):
    #     nonlocal pos
    #     nonlocal text
    #     items = {}
    #     for i in range(nitems):
    #         token, token2 = next()
    #         if not token:
    #             return items
    #         name = token2
    #         token, token2 = next()
    #         if token[0] == 'N':
    #             items[name] = None
    #         elif token[0] == 'n':
    #             items[name] = False
    #         elif token[0] == 'y':
    #             items[name] = True
    #         elif token[0] == 'i':
    #             items[name] = int(token2[1:])
    #         elif token[0] == 'f':
    #             items[name] = float(token2[1:])
    #         elif token[0] == 's':
    #             n = int(token2[1:])
    #             parts = [token[len(token2)+1:]]
    #             count = len(parts[0])
    #             while count < n:
    #                 tok, _ = next()
    #                 count += len(tok)
    #                 parts.append(tok)
    #             if count > n:
    #                 parts[-1] = parts[-1][:-(count-n)]
    #             items[name] = ''.join(parts)
    #         elif token[0] == 'L':
    #             n = int(token2[1:])
    #             items[name] = decode_list(n)
    #         elif token[0] == 'D':
    #             n = int(token2[1:])
    #             items[name] = decode_dict(n)
    #         else:
    #             raise RuntimeError('Unexpected chars: ' + token)
    #     return items
    # 
    # def decode_list(nitems):
    #     nonlocal pos
    #     nonlocal text
    #     items = []
    #     for i in range(nitems):
    #         token, token2 = next()
    #         if not token:
    #             return items
    #         if token[0] == 'N':
    #             items.append(None)
    #         elif token[0] == 'n':
    #             items.append(False)
    #         elif token[0] == 'y':
    #             items.append(True)
    #         elif token[0] == 'i':
    #             items.append(int(token2[1:]))
    #         elif token[0] == 'f':
    #             items.append(float(token2[1:]))
    #         elif token[0] == 's':
    #             n = int(token2[1:])
    #             parts = [token[len(token2)+1:]]
    #             count = len(parts[0])
    #             while count < n:
    #                 tok, _ = next()
    #                 count += len(tok)
    #                 parts.append(tok)
    #             if count > n:
    #                 parts[-1] = parts[-1][:-(count-n)]
    #             items.append(''.join(parts))
    #         elif token[0] == 'L':
    #             n = int(token2[1:])
    #             items.append(decode_list(n))
    #         elif token[0] == 'D':
    #             n = int(token2[1:])
    #             items.append(decode_dict(n))
    #     return items
    
    return loads

loads = make_decoder()
