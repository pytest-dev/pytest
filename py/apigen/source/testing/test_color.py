import py
from py.__.apigen.source.color import Tokenizer, Token, PythonSchema

class TestTokenizer(object):
    def tokens(self, data):
        t = Tokenizer(PythonSchema)
        return list(t.tokenize(data))

    def test_word(self):
        assert self.tokens('foo') == [Token('foo', type='word')]
        assert self.tokens('_1_word') == [Token('_1_word', type='word')]

    def test_keyword(self):
        assert 'if' in PythonSchema.keyword
        assert self.tokens('see if it works') == [Token('see', type='word'),
                                                  Token(' ',
                                                        type='whitespace'),
                                                  Token('if', type='keyword'),
                                                  Token(' ',
                                                        type='whitespace'),
                                                  Token('it', type='word'),
                                                  Token(' ',
                                                        type='whitespace'),
                                                  Token('works', type='word')]

    def test_space(self):
        assert self.tokens(' ') == [Token(' ', type='whitespace')]
        assert self.tokens(' \n') == [Token(' \n', type='whitespace')]

    def test_number(self):
        # XXX incomplete
        assert self.tokens('1') == [Token('1', type='number')]
        assert self.tokens('1.1') == [Token('1.1', type='number')]
        assert self.tokens('.1') == [Token('.1', type='number')]
        assert self.tokens('1.') == [Token('1.', type='number')]
        assert self.tokens('1.1l') == [Token('1.1l', type='number')]

    def test_printable(self):
        assert self.tokens('.') == [Token('.', 'unknown')]
        assert self.tokens(';#$@\n') == [Token(';#$@', type='unknown'),
                                         Token('\n', type='whitespace')]

    def test_comment(self):
        assert self.tokens('# foo\n') == [Token('# foo\n', type='comment')]
        assert self.tokens('foo # bar\n') == [Token('foo', type='word'),
                                              Token(' ', type='whitespace'),
                                              Token('# bar\n', type='comment')]
        assert self.tokens("# foo 'bar\n") == [Token("# foo 'bar\n",
                                                     type='comment')]
        assert self.tokens('# foo') == [Token('# foo', type='comment')]

    def test_string_simple(self):
        assert self.tokens('""') == [Token('""', type='string')]
        assert self.tokens('"foo"') == [Token('"foo"', type='string')]
        assert self.tokens('"foo"\'bar\'') == [Token('"foo"', type='string'),
                                               Token("'bar'", type='string')]

    def test_string_escape(self):
        assert self.tokens('"foo \\" bar"') == [Token('"foo \\" bar"',
                                                      type='string')]

    def test_string_multiline(self):
        t = Tokenizer(PythonSchema)
        res = list(t.tokenize('"""foo\n'))
        assert res == [Token('"""foo\n', type='string')]
        res = list(t.tokenize('bar\n'))
        assert res == [Token('bar\n', type='string')]
        res = list(t.tokenize('"""\n'))
        assert res == [Token('"""', type='string'),
                       Token('\n', type='whitespace')]
        # tricky problem: the following line must not put the tokenizer in
        # 'multiline state'...
        res = list(t.tokenize('"""foo"""'))
        assert res == [Token('"""foo"""', type='string')]
        res = list(t.tokenize('bar'))
        assert res == [Token('bar', type='word')]

    def test_string_multiline_slash(self):
        t = Tokenizer(PythonSchema)
        res = list(t.tokenize("'foo\\"))
        assert res == [Token("'foo\\", type='string')]
        res = list(t.tokenize("bar'"))
        assert res == [Token("bar'", type='string')]
        res = list(t.tokenize("bar"))
        assert res == [Token('bar', type='word')]
        res = list(t.tokenize('"foo\\bar"'))
        assert res == [Token('"foo\\bar"', type="string")]

    def test_string_following_printable(self):
        assert self.tokens('."foo"') == [Token('.', type='unknown'),
                                         Token('"foo"', type='string')]

    def test_something_strange(self):
        t = Tokenizer(PythonSchema)
        tokens = list(t.tokenize('"""foo "bar" baz"""'))
        assert not t._inside_multiline

