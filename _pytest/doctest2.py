import doctest
import itertools as it
import ast
import sys
import tokenize

if sys.version_info.major == 3:
    from io import StringIO
else:
    import cStringIO as StringIO


def testdata():
    self = DocTestParser2()
    name = '<string>'
    string = '''
            text
            >>> dsrc()
            want

                >>> dsrc()
                >>> cont(
                ... a=b)
                ... dsrc
                >>> dsrc():
                ...     a
                ...     b = """
                        multiline
                        """
                want

            text
            ... still text
            >>> "now its a doctest"

            text
    '''
    self.parse(string, name)

    import ubelt as ub
    string = ub.codeblock(
        '''
            .. doctest::

                >>> print(
                ...    "Hi\\n\\nByé")
                Hi
                ...
                Byé
                >>> 1/0  # Byé
                1
        ''')
    import doctest
    self2 = DocTestParser2()
    self1 = doctest.DocTestParser()
    self2._label_lines(string)

    string = ub.codeblock(
        """
        .. doctest::

            >>> '''
                multiline strings are now kosher
                '''
            multiline strings are now kosher
        """)

    string = ub.codeblock(
        """
        .. doctest::

            >>> x = y
            ... foo = bar
        """)

    string = ub.codeblock(
        '''
        text-line-1
        text-line-2
        text-line-3
        text-line-4
        text-line-5
        text-line-6
        text-line-7
        text-line-8
        text-line-9
        text-line-10
        text-line-11
        >>> 1 + 1
        3

        text-line-after
        ''')

    import doctest
    import ubelt as ub
    self1 = doctest.DocTestParser()
    self2 = DocTestParser2()
    self2._label_lines(string)
    print('\n==== PARSER2 ====')
    for x, o in enumerate(self2.parse(string, '')):
        print('----')
        print(x)
        if not isinstance(o, str):
            print(ub.repr2(o.__dict__))
            # print('o.source = {!r}'.format(o.source))
            # print('o.want = {!r}'.format(o.want))
        else:
            print('o = {!r}'.format(o))
    print('\n==== PARSER1 ====')
    for x, o in enumerate(self1.parse(string, '')):
        print('----')
        print(x)
        if not isinstance(o, str):
            print(ub.repr2(o.__dict__))
            # print('o.source = {!r}'.format(o.source))
            # print('o.want = {!r}'.format(o.want))
        else:
            print('o = {!r}'.format(o))

    string = ub.codeblock(
        """
        .. doctest::

            >>> '''
                multiline strings are now kosher
                '''
            multiline strings are now kosher
        """)

    string = ub.codeblock(
        '''
        >>> import os
        >>> os.environ["HELLO"]
        'WORLD'
        ''')
    self = DocTestParser2()
    self._label_lines(string)
    ex = self.parse(string, '')[0]

    outputs = self2.parse(string, name='<string>')
    print('outputs = {!r}'.format(outputs))
    for o in outputs:
        if not isinstance(o, str):
            e = o
            print('e.source = {!r}'.format(e.source))
            print('e.want = {!r}'.format(e.want))

    source = ub.codeblock(
            '''
            a = b; b = c
            def foo():
                pass
                pass
            try:
                a = b
            except Exception as ex:
                pass
            else:
                pass
            class X:
                def foo():
                    pass
            ''')
    import ast
    pt = ast.parse(source)
    ps1_linenos = sorted({node.lineno for node in pt.body})


class DocTestParser2(doctest.DocTestParser):
    """
    CommandLine:
        pytest testing/test_doctest.py
        pytest testing/test_doctest.py::TestDoctests::test_unicode_doctest

    Example:
        >>> from textwrap import dedent
        >>> self = DocTestParser2()
        >>> string = dedent(
            '''
            This is Doctest Inception: An example doctest IN A DOCTEST.
            >>> print('foobar')
            >>> def multilines():
            ...     arent_the_most_intuitive_in_standard_doctests()
            >>> but_now_you_can_define_lists = [
            >>>     'without',
            >>>     'having to worry',
            >>> ]
            want statments still work fine

            parse it into multiple parts just fine

            ''')
        >>> print(string)
    """

    def _label_lines(self, string):
        """
        >>> from _pytest.doctest2 import *
        >>> import textwrap
        >>> self = DocTestParser2()
        >>> # Having multiline strings in doctests can be nice
        >>> string = textwrap.dedent(
                '''
                text
                >>> items = ['also', 'nice', 'to', 'not', 'worry',
                >>>          'about', '...', 'vs', '>>>']
                ... print('but its still allowed')
                but its still allowed

                more text
                ''').strip()
        >>> self._label_lines(string)
        [('text', 'text'),
         ('dsrc', ">>> items = ['also', 'nice', 'to', 'not', 'worry', 'about',"),
         ('dsrc', ">>>          'using', '...', 'instead', 'of', '>>>']"),
         ('dsrc', "... print('but its still allowed')"),
         ('want', 'but its still allowed'),
         ('want', ''),
         ('want', 'more text')]
        """

        def _complete_source(line, state_indent, line_iter):
            """
            helper
            remove lines from the iterator if they are needed to complete source
            """

            norm_line = line[state_indent:]  # Normalize line indentation
            prefix = norm_line[:4]
            suffix = norm_line[4:]
            assert prefix.strip() in {'>>>', '...'}, '{}'.format(prefix)
            yield line

            source_parts = [suffix]
            while not is_balanced(source_parts):
                try:
                    linex, next_line = next(line_iter)
                except StopIteration:
                    raise SyntaxError('ill-formed doctest')
                norm_line = next_line[state_indent:]
                prefix = norm_line[:4]
                suffix = norm_line[4:]
                if prefix.strip() not in {'>>>', '...', ''}:  # nocover
                    raise SyntaxError(
                        'Bad indentation in doctest on line {}: {!r}'.format(
                            linex, next_line))
                source_parts.append(suffix)
                yield next_line

        # parse and differenatiate between doctest source and want statements.
        labeled_lines = []
        state_indent = 0

        # states
        TEXT = 'text'
        DSRC = 'dsrc'
        WANT = 'want'

        # Move through states, keeping track of points where states change
        #     text -> [text, dsrc]
        #     dsrc -> [dsrc, want, text]
        #     want -> [want, text, dsrc]
        prev_state = TEXT
        curr_state = None
        line_iter = enumerate(string.splitlines())
        for linex, line in line_iter:
            match = self._INDENT_RE.search(line)
            line_indent = 0 if match is None else (match.end() - match.start())
            norm_line = line[state_indent:]  # Normalize line indentation
            strip_line = line.strip()

            # Check prev_state transitions
            if prev_state == TEXT:
                # text transitions to source whenever a PS1 line is encountered
                # the PS1(>>>) can be at an arbitrary indentation
                if strip_line.startswith('>>> '):
                    curr_state = DSRC
                else:
                    curr_state = TEXT
            elif prev_state == WANT:
                # blank lines terminate wants
                if len(strip_line) == 0:
                    curr_state = TEXT
                # source-inconsistent indentation terminates want
                elif line.strip().startswith('>>> '):
                    curr_state = DSRC
                elif line_indent < state_indent:
                    curr_state = TEXT
                else:
                    curr_state = WANT
            elif prev_state == DSRC:
                if len(strip_line) == 0 or line_indent < state_indent:
                    curr_state = TEXT
                # allow source to continue with either PS1 or PS2
                elif norm_line.startswith(('>>> ', '... ')):
                    if strip_line == '...':
                        curr_state = WANT
                    else:
                        curr_state = DSRC
                else:
                    curr_state = WANT

            # Handle transitions
            if prev_state != curr_state:
                # Handle start of new states
                if curr_state == TEXT:
                    state_indent = 0
                if curr_state == DSRC:
                    # Start a new source
                    state_indent = line_indent
                    # renormalize line when indentation changes
                    norm_line = line[state_indent:]

            # continue current state
            if curr_state == DSRC:
                # source parts may consume more than one line
                for part in _complete_source(line, state_indent, line_iter):
                    labeled_lines.append((DSRC, part))
            elif curr_state == WANT:
                labeled_lines.append((WANT, line))
            elif curr_state == TEXT:
                labeled_lines.append((TEXT, line))
            prev_state = curr_state

        return labeled_lines

    def _parse_example(self, m, name, lineno):
        raise NotImplementedError('not needed in verion 2')

    def parse(self, string, name='<string>'):
        """
        Divide the given string into examples and intervening text,
        and return them as a list of alternating Examples and strings.
        Line numbers for the Examples are 0-based.  The optional
        argument `name` is a name identifying this string, and is only
        used for error messages.
        """
        string = string.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = self._min_indent(string)
        if min_indent > 0:
            string = '\n'.join([l[min_indent:] for l in string.split('\n')])

        labeled_lines = self._label_lines(string)

        # Now that lines have types, group them. This could have done this
        # above, but functinoality is split for readability.
        prev_source = None
        grouped_output = []
        for state, group in it.groupby(labeled_lines, lambda t: t[0]):
            block = [t[1] for t in group]
            if state == 'text':
                if prev_source is not None:
                    # accept a source block without a want block
                    grouped_output.append((prev_source, ''))
                    prev_source = None
                # accept the text
                grouped_output.append(block)
            elif state == 'want':
                assert prev_source is not None, 'impossible'
                grouped_output.append((prev_source, block))
                prev_source = None
            elif state == 'dsrc':
                # need to check if there is a want after us
                prev_source = block
        # Case where last block is source
        if prev_source:
            grouped_output.append((prev_source, ''))

        lineno = 0
        output = []
        for chunk in grouped_output:
            if isinstance(chunk, tuple):
                source_lines, want_lines = chunk

                match = self._INDENT_RE.search(source_lines[0])
                line_indent = 0 if match is None else (match.end() - match.start())
                indent = min_indent + line_indent

                # Strip indentation (and PS1 / PS2 from source)
                norm_source_lines = [p[line_indent + 4:] for p in source_lines]

                source_block = '\n'.join(norm_source_lines)
                # for compatibility we break down each source block into
                # individual statements. (We need to remember to move PS2 lines
                # in with the previous PS1 line)
                pt = ast.parse(source_block)
                ps1_linenos = [node.lineno - 1 for node in pt.body]
                NEED_16806_WORKAROUND = True
                if NEED_16806_WORKAROUND:
                    # WORKAROUND FOR PYTHON ISSUE 16806 (https://bugs.python.org/issue16806)
                    # Issue causes lineno for multiline strings to give the
                    # line they end on, not the line they start on.
                    # Note: patch for this issue exists https://github.com/python/cpython/pull/1800
                    #
                    # Workaround:
                    # Starting from the end look at consecutive pairs of
                    # indices to inspect the statment it corresponds to.
                    # (the first statment goes from ps1_linenos[-1] to the end
                    # of the line list.
                    new_ps1_lines = []
                    b = len(norm_source_lines)
                    for a in ps1_linenos[::-1]:
                        # the position of `b` is correct, but `a` may be wrong
                        # is_balanced will be False iff `a` is wrong.
                        while not is_balanced(norm_source_lines[a:b]):
                            # shift `a` down until it becomes correct
                            a -= 1
                        # push the new correct value back into the list
                        new_ps1_lines.append(a)
                        # set the end position of the next string to be `a` ,
                        # note, because this `a` is correct, the next `b` is
                        # must also be correct.
                        b = a
                    ps1_linenos = set(new_ps1_lines)
                    # Proof of correctness:
                    #     Check each group of lines in the range a:b We
                    #     iteravely assign `a` to the start position (starting
                    #     from the back of the `ps1_linenos` list) We must
                    #     initially set `b` to be the number of lines.  We are
                    #     garuenteed that `b` is correct (because the last
                    #     statment must end on the last line), but `a` may be
                    #     wrong. Therefore, we check if lines[a:b] are
                    #     balanced, if not then this must be a bugged multiline
                    #     string. We decrease `a` until the statment is
                    #     balanced. This must be the true start of the
                    #     multiline string. Now, we know a and b are valid
                    #     positions. Push `a` onto a new list, then set `a=b`.
                    #     Remove the processed statement, and set `a` to the
                    #     new end of `ps1_linenos`. Now, by the same
                    #     (inductive) argument, the "decreasing balanced check"
                    #     will find the right value of a and b for this
                    #     newline. This continues until all lines are procesed.
                    #     The final result is we know the real starting
                    #     position of every ps1_line.
                ps2_linenos = {
                    x for x, p in enumerate(source_lines)
                    if p[line_indent:line_indent + 4] != '>>> '
                }
                ps1_linenos = sorted(ps1_linenos.difference(ps2_linenos))

                # Break down first parts which dont have any want
                for s1, s2 in zip(ps1_linenos, ps1_linenos[1:]):
                    source = '\n'.join(norm_source_lines[s1:s2])
                    options = self._find_options(source, name, lineno + s1)
                    example = doctest.Example(
                        source, '', None, lineno=lineno + s1,
                        indent=indent, options=options)
                    output.append(example)

                # the last part has a want
                last = ps1_linenos[-1]
                source = '\n'.join(norm_source_lines[last:])
                # If `want` contains a traceback message, then extract it.
                norm_want_lines = [p[line_indent:] for p in want_lines]
                want = '\n'.join(norm_want_lines)
                m = self._EXCEPTION_RE.match(want)
                if m:
                    exc_msg = m.group('msg')
                else:
                    exc_msg = None

                options = self._find_options(source, name, lineno + last)

                example = doctest.Example(
                    source, want, exc_msg, lineno=lineno + last,
                    indent=indent, options=options)
                output.append(example)
                lineno += len(source_lines)
            else:
                output.append('\n'.join(chunk))
                lineno += len(chunk)
        return output


def is_balanced(lines):
    """
    Checks if the lines have balanced parens, brakets, curlies and strings

    Args:
        lines (list): list of strings

    Returns:
        bool : True if statment has balanced containers

    Doctest:
        >>> assert is_balanced(['print(foobar)'])
        >>> assert is_balanced(['foo = bar']) is True
        >>> assert is_balanced(['foo = (']) is False
        >>> assert is_balanced(['foo = (', "')(')"]) is True
        >>> assert is_balanced(
        ...     ['foo = (', "'''", ")]'''", ')']) is True
    """
    if sys.version_info.major == 3:
        block = '\n'.join(lines)
    else:
        block = '\n'.join(lines).encode('utf8')
    stream = StringIO()
    stream.write(block)
    stream.seek(0)
    try:
        for t in tokenize.generate_tokens(stream.readline):
            pass
    except tokenize.TokenError as ex:
        message = ex.args[0]
        if message.startswith('EOF in multi-line'):
            return False
        raise
    else:
        return True


# if False:
#     import ubelt as ub
#     source_lines = ub.codeblock(
#             '''
#             >>> a = b; b = c
#             >>> def foo():
#             >>>     pass
#             >>>     pass
#             >>> try:
#             >>>     a = b
#             >>> except Exception as ex:
#             >>>     pass
#             >>> else:
#             >>>     pass
#             >>> class X:
#             >>>     def foo():
#             >>>         pass
#             >>> e = f
#             ... g = h
#             ... print('foo')
#             >>> one = """
#                 foobar
#                 """
#             >>> two
#             ''').splitlines()
#     # source_lines = ['    >>> 1/0  # Byé']
#     # want_lines = ['    1']
#     want_lines = []
#     self = DocTestParser2()
#     min_indent = 0
#     source_lines = ub.codeblock(
#         """
#         01  >>> ['''
#         02       pathological, but no problem''',
#         03  >>>  2]
#         04  >>> '''
#         05      multiline strings are now kosher
#         06      '''
#         07  >>> '''
#         08      this may throw a wrench in the workaround
#         x9      '''
#         10  >>> a = b
#         11  ... b = c
#         12  ... c = d
#         10  >>> '''
#         11      multiline strings are now kosher
#         12      '''
#         13  >>> y = '''
#         14      multiline strings are now kosher
#         15      '''
#         16  >>> ('''
#         17      multiline strings are now kosher
#         18      ''',)
#         19  >>> ['''
#         20      multiline strings are now kosher
#         21      ''',]
#         22  >>> '''
#         23      multiline strings are now kosher
#         24      '''
#         """).splitlines()
#     norm_source_lines = [p[8:] for p in source_lines]
#     source_lines = ub.codeblock(
#         """
#         >>> '''
#             multiline strings are now kosher
#             '''
#         """).splitlines()
#     source_lines = ub.codeblock(
#         """
#         >>> '''
#             multiline strings are now kosher
#             '''
#         ... '''
#             multiline strings are now kosher
#             '''
#         """).splitlines()
#     norm_source_lines = [p[4:] for p in source_lines]
#     source_block = '\n'.join(norm_source_lines)
#     pt = ast.parse(source_block)
#     for node in pt.body:
#         print('{} {}'.format(type(node), ub.repr2(node.__dict__, nl=1)))

