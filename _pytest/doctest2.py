import doctest
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
    self2 = DocTestParser2()
    self1 = doctest.DocTestParser()
    self2._label_lines(string)

    print('========')
    for x, o in enumerate(self2.parse(string, '')):
        print('----')
        print(x)
        if not isinstance(o, str):
            print('o.source = {!r}'.format(o.source))
            print('o.want = {!r}'.format(o.want))
        else:
            print(o)
    print('========')
    for x, o in enumerate(self1.parse(string, '')):
        print('----')
        print(x)
        if not isinstance(o, str):
            print('o.source = {!r}'.format(o.source))
            print('o.want = {!r}'.format(o.want))
        else:
            print(o)


    string = ub.codeblock(
        '''
        >>> import os
        >>> os.environ["HELLO"]
        'WORLD'
        ''')
    self = DocTestParser2()
    self._label_lines(string)
    ex = self.parse(string, '')[0]

    import doctest
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
        Move through states, keeping track of points where states change
            text -> [text, source_part, source]
            source_part -> [source_part, source]
            source -> [source, source_part,  want, text]
            want -> [want, text, source_part, source]
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
        prev_state = 'text'
        curr_state = None
        line_iter = enumerate(string.splitlines())
        for linex, line in line_iter:
            match = self._INDENT_RE.search(line)
            line_indent = 0 if match is None else (match.end() - match.start())
            norm_line = line[state_indent:]  # Normalize line indentation
            strip_line = line.strip()

            # Check prev_state transitions
            if prev_state == 'text':
                # text transitions to source whenever a PS1 line is encountered
                # the PS1(>>>) can be at an arbitrary indentation
                if strip_line.startswith('>>> '):
                    curr_state = 'dsrc'
                else:
                    curr_state = 'text'
            elif prev_state == 'want':
                # blank lines terminate wants
                if len(strip_line) == 0:
                    curr_state = 'text'
                # source-inconsistent indentation terminates want
                if line.strip().startswith('>>> '):
                    curr_state = 'dsrc'
                elif line_indent < state_indent:
                    curr_state = 'text'
                else:
                    curr_state = 'want'
            elif prev_state == 'dsrc':
                if len(strip_line) == 0 or line_indent < state_indent:
                    curr_state = 'text'
                # allow source to continue with either PS1 or PS2
                elif norm_line.startswith(('>>> ', '... ')):
                    curr_state = 'dsrc'
                else:
                    curr_state = 'want'

            # Handle transitions
            if prev_state != curr_state:
                # Handle start of new states
                if curr_state == 'text':
                    state_indent = 0
                if curr_state == 'dsrc':
                    # Start a new source
                    state_indent = line_indent
                    # renormalize line when indentation changes
                    norm_line = line[state_indent:]

            # continue current state
            if curr_state == 'dsrc':
                # source parts may consume more than one line
                for part in _complete_source(line, state_indent, line_iter):
                    labeled_lines.append(('dsrc', part))
            elif curr_state == 'want':
                labeled_lines.append(('want', line))
            elif curr_state == 'text':
                labeled_lines.append(('text', line))
            prev_state = curr_state

        return labeled_lines

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
        import itertools as it
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
                if False:
                    want_lines = []
                    import ubelt as ub
                    source_lines = ub.codeblock(
                            '''
                            >>> a = b; b = c
                            >>> def foo():
                            >>>     pass
                            >>>     pass
                            >>> try:
                            >>>     a = b
                            >>> except Exception as ex:
                            >>>     pass
                            >>> else:
                            >>>     pass
                            >>> class X:
                            >>>     def foo():
                            >>>         pass
                            >>> e = f
                            ... g = h
                            ... print('foo')
                            >>> one = """
                                foobar
                                """
                            >>> two
                            ''').splitlines()
                    # source_lines = ['    >>> 1/0  # Byé']
                    # want_lines = ['    1']
                source_lines, want_lines = chunk

                match = self._INDENT_RE.search(source_lines[0])
                line_indent = 0 if match is None else (match.end() - match.start())
                indent = min_indent + line_indent

                # Strip indentation (and PS1 / PS2 from source)
                norm_source_lines = [p[line_indent + 4:] for p in source_lines]
                norm_want_lines = [p[line_indent:] for p in want_lines]

                source_block = '\n'.join(norm_source_lines)

                # for compatibility we break down each source block into
                # individual statements. (We need to remember to move PS2 lines
                # in with the previous PS1 line)
                import ast
                pt = ast.parse(source_block)
                ps1_linenos = {node.lineno - 1 for node in pt.body}
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
        >>> from ubelt.meta.static_analysis import *  # NOQA
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


def parse_src_want(string):
    """
    Breaks into sections of source code and result checks

    Args:
        string (str):

    CommandLine:
        python -m ubelt.util_test parse_src_want

    References:
        https://stackoverflow.com/questions/46061949/parse-until-expr-complete

    Example:
        >>> from ubelt.util_test import *  # NOQA
        >>> from ubelt.meta import docscrape_google
        >>> import inspect
        >>> docstr = inspect.getdoc(parse_src_want)
        >>> blocks = dict(docscrape_google.split_google_docblocks(docstr))
        >>> string = blocks['Example']
        >>> src, want = parse_src_want(string)
        >>> 'I want to see this str'
        I want to see this str

    Example:
        >>> from ubelt.util_test import *  # NOQA
        >>> from ubelt.meta import docscrape_google
        >>> import inspect
        >>> docstr = inspect.getdoc(parse_src_want)
        >>> blocks = dict(docscrape_google.split_google_docblocks(docstr))
        >>> str = (
            '''
            TODO: be able to parse docstrings like this.
            ''')
        >>> print('Intermediate want')
        Intermediate want
        >>> string = blocks['Example']
        >>> src, want = parse_src_want(string)
        >>> 'I want to see this str'
        I want to see this str
    """
    # parse and differenatiate between doctest source and want statements.
    parsed = []
    current = []
    for linex, line in enumerate(string.splitlines()):
        if not current and not line.startswith(('>>>', '...')):
            parsed.append(('want', line))
        else:
            prefix = line[:4]
            suffix = line[4:]
            if prefix.strip() not in {'>>>', '...', ''}:  # nocover
                raise SyntaxError(
                    'Bad indentation in doctest on line {}: {!r}'.format(
                        linex, line))
            current.append(suffix)
            if static.is_balanced(current):
                statement = ('\n'.join(current))
                parsed.append(('source', statement))
                current = []
