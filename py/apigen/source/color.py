""" simple Python syntax coloring """

import re

class PythonSchema(object):
    """ contains information for syntax coloring """
    comment = [('#', '\n'), ('#', '$')]
    multiline_string = ['"""', "'''"]
    string = ['"""', "'''", '"', "'"]
    keyword = ['and', 'break', 'continue', 'elif', 'else', 'except',
               'finally', 'for', 'if', 'in', 'is', 'not', 'or', 'raise',
               'return', 'try', 'while', 'with', 'yield']
    alt_keyword = ['as', 'assert', 'class', 'def', 'del', 'exec', 'from',
                   'global', 'import', 'lambda', 'pass', 'print']
    linejoin = r'\\'

def assert_keywords():
    from keyword import kwlist
    all = PythonSchema.keyword + PythonSchema.alt_keyword
    for x in kwlist:
        assert x in all
assert_keywords()

class Token(object):
    data = None
    type = 'unknown'

    def __init__(self, data, type='unknown'):
        self.data = data
        self.type = type

    def __repr__(self):
        return '<Token type="%s" %r>' % (self.type, self.data)

    def __eq__(self, other):
        return self.data == other.data and self.type == other.type

    def __ne__(self, other):
        return not self.__eq__(other)

class Tokenizer(object):
    """ when fed lists strings, it will return tokens with type info
    
        very naive tokenizer, state is recorded for multi-line strings, etc.
    """

    _re_word = re.compile('[\w_]+', re.U)
    _re_space = re.compile('\s+', re.U)
    _re_number = re.compile('[\d\.]*\d[\d\.]*l?', re.I | re.U)
    # XXX cheating a bit with the quotes
    _re_rest = re.compile('[^\w\s\d\'"]+', re.U)

    # these will be filled using the schema
    _re_strings_full = None
    _re_strings_multiline = None
    _re_strings_comments = None

    def __init__(self, schema):
        self.schema = schema
        self._inside_multiline = False
        
        self._re_strings_full = []
        self._re_strings_multiline = []
        self._re_strings_empty = []
        for d in schema.string + schema.multiline_string:
            self._re_strings_full.append(
                re.compile(r'%s[^\\%s]*(\\.[^\\%s]*)+%s' % (d, d, d, d)))
            self._re_strings_full.append(
                re.compile(r'%s[^\\%s]+(\\.[^\\%s]*)*%s' % (d, d, d, d)))
            self._re_strings_empty.append(re.compile('%s%s' % (d, d)))
        for d in schema.multiline_string:
            self._re_strings_multiline.append((re.compile('(%s).*' % (d,),
                                                          re.S),
                                               re.compile('.*?%s' % (d,))))
        if schema.linejoin:
            j = schema.linejoin
            for d in schema.string:
                self._re_strings_multiline.append(
                    (re.compile('(%s).*%s$' % (d, j)),
                     re.compile('.*?%s' % (d,))))
        # no multi-line comments in Python... phew :)
        self._re_comments = []
        for start, end in schema.comment:
            self._re_comments.append(re.compile('%s.*?%s' % (start, end)))

    def tokenize(self, data):
        if self._inside_multiline:
            m = self._inside_multiline.match(data)
            if not m:
                yield Token(data, 'string')
                data = ''
            else:
                s = m.group(0)
                data = data[len(s):]
                self._inside_multiline = False
                yield Token(s, 'string')
        while data:
            for f in [self._check_full_strings, self._check_multiline_strings,
                      self._check_empty_strings, self._check_comments,
                      self._check_number, self._check_space, self._check_word,
                      self._check_rest]:
                data, t = f(data)
                if t:
                    yield t
                    break
            else:
                raise ValueError(
                        'no token found in %r (bug in tokenizer)' % (data,))
                
    def _check_full_strings(self, data):
        token = None
        for r in self._re_strings_full:
            m = r.match(data)
            if m:
                s = m.group(0)
                data = data[len(s):]
                token = Token(s, type='string')
                break
        return data, token

    def _check_multiline_strings(self, data):
        token = None
        for start, end in self._re_strings_multiline:
            m = start.match(data)
            if m:
                s = m.group(0)
                data = ''
                # XXX take care of a problem which is hard to fix with regexps:
                # '''foo 'bar' baz''' will not match single-line strings
                # (because [^"""] matches just a single " already), so let's
                # try to catch it here... (quite Python specific issue!)
                endm = end.match(s[len(m.group(1)):])
                if endm: # see if it ends here already
                    s = m.group(1) + endm.group(0)
                else:
                    self._inside_multiline = end
                token = Token(s, 'string')
                break
        return data, token

    def _check_empty_strings(self, data):
        token = None
        for r in self._re_strings_empty:
            m = r.match(data)
            if m:
                s = m.group(0)
                data = data[len(s):]
                token = Token(s, type='string')
                break
        return data, token

    def _check_comments(self, data):
        # fortunately we don't have to deal with multi-line comments
        token = None
        for r in self._re_comments:
            m = r.match(data)
            if m:
                s = m.group(0)
                data = data[len(s):]
                token = Token(s, 'comment')
                break
        return data, token

    def _check_word(self, data):
        m = self._re_word.match(data)
        if m:
            s = m.group(0)
            type = 'word'
            if s in self.schema.keyword:
                type = 'keyword'
            elif s in self.schema.alt_keyword:
                type = 'alt_keyword'
            return data[len(s):], Token(s, type)
        return data, None

    def _check_space(self, data):
        m = self._re_space.match(data)
        if m:
            s = m.group(0)
            return data[len(s):], Token(s, 'whitespace')
        return data, None

    def _check_number(self, data):
        m = self._re_number.match(data)
        if m:
            s = m.group(0)
            return data[len(s):], Token(s, 'number')
        return data, None

    def _check_rest(self, data):
        m = self._re_rest.match(data)
        if m:
            s = m.group(0)
            return data[len(s):], Token(s, 'unknown')
        return data, None

if __name__ == '__main__':
    import py, sys
    if len(sys.argv) != 2:
        print 'usage: %s <filename>'
        print '  tokenizes the file and prints the tokens per line'
        sys.exit(1)
    t = Tokenizer(PythonSchema)
    p = py.path.local(sys.argv[1])
    assert p.ext == '.py'
    for line in p.read().split('\n'):
        print repr(line)
        print 't in multiline mode:', not not t._inside_multiline
        tokens = t.tokenize(line)
        print list(tokens)

