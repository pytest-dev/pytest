import py

class RestdocPlugin:
    def pytest_addoption(self, parser):
        group = parser.addgroup("ReST", "ReST documentation check options")
        group.addoption('-R', '--urlcheck',
               action="store_true", dest="urlcheck", default=False, 
               help="urlopen() remote links found in ReST text files.") 
        group.addoption('--urltimeout', action="store", metavar="secs",
            type="int", dest="urlcheck_timeout", default=5,
            help="timeout in seconds for remote urlchecks")
        group.addoption('--forcegen',
               action="store_true", dest="forcegen", default=False,
               help="force generation of html files.")

    def pytest_collect_file(self, path, parent):
        if path.ext == ".txt":
            project = getproject(path)
            if project is not None:
                return ReSTFile(path, parent=parent, project=project)

def getproject(path):
    for parent in path.parts(reverse=True):
        confrest = parent.join("confrest.py")
        if confrest.check():
            Project = confrest.pyimport().Project
            return Project(parent)

class ReSTFile(py.test.collect.File):
    def __init__(self, fspath, parent, project=None):
        super(ReSTFile, self).__init__(fspath=fspath, parent=parent)
        if project is None:
            project = getproject(fspath)
            assert project is not None
        self.project = project

    def collect(self):
        return [
            ReSTSyntaxTest(self.project, "ReSTSyntax", parent=self),
            LinkCheckerMaker("checklinks", parent=self),
            DoctestText("doctest", parent=self),
        ]

def deindent(s, sep='\n'):
    leastspaces = -1
    lines = s.split(sep)
    for line in lines:
        if not line.strip():
            continue
        spaces = len(line) - len(line.lstrip())
        if leastspaces == -1 or spaces < leastspaces:
            leastspaces = spaces
    if leastspaces == -1:
        return s
    for i, line in py.builtin.enumerate(lines):
        if not line.strip():
            lines[i] = ''
        else:
            lines[i] = line[leastspaces:]
    return sep.join(lines)

class ReSTSyntaxTest(py.test.collect.Item): 
    def __init__(self, project, *args, **kwargs):
        super(ReSTSyntaxTest, self).__init__(*args, **kwargs)
        self.project = project

    def runtest(self):
        self.restcheck(py.path.svnwc(self.fspath))

    def restcheck(self, path):
        py.test.importorskip("docutils")
        self.register_linkrole()
        from docutils.utils import SystemMessage
        try: 
            self._checkskip(path, self.project.get_htmloutputpath(path))
            self.project.process(path)
        except KeyboardInterrupt: 
            raise 
        except SystemMessage: 
            # we assume docutils printed info on stdout 
            py.test.fail("docutils processing failed, see captured stderr") 

    def register_linkrole(self):
        from py.__.rest import directive
        directive.register_linkrole('api', self.resolve_linkrole)
        directive.register_linkrole('source', self.resolve_linkrole)

        # XXX fake sphinx' "toctree" and refs
        directive.register_linkrole('ref', self.resolve_linkrole)
        
        from docutils.parsers.rst import directives
        def toctree_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
            return []
        toctree_directive.content = 1
        toctree_directive.options = {'maxdepth': int, 'glob': directives.flag,
                             'hidden': directives.flag}
        directives.register_directive('toctree', toctree_directive)

    def resolve_linkrole(self, name, text, check=True):
        apigen_relpath = self.project.apigen_relpath
    
        if name == 'api':
            if text == 'py':
                return ('py', apigen_relpath + 'api/index.html')
            else:
                assert text.startswith('py.'), (
                    'api link "%s" does not point to the py package') % (text,)
                dotted_name = text
                if dotted_name.find('(') > -1:
                    dotted_name = dotted_name[:text.find('(')]
                # remove pkg root
                path = dotted_name.split('.')[1:]
                dotted_name = '.'.join(path)
                obj = py
                if check:
                    for chunk in path:
                        try:
                            obj = getattr(obj, chunk)
                        except AttributeError:
                            raise AssertionError(
                                'problem with linkrole :api:`%s`: can not resolve '
                                'dotted name %s' % (text, dotted_name,))
                return (text, apigen_relpath + 'api/%s.html' % (dotted_name,))
        elif name == 'source':
            assert text.startswith('py/'), ('source link "%s" does not point '
                                            'to the py package') % (text,)
            relpath = '/'.join(text.split('/')[1:])
            if check:
                pkgroot = py.__pkg__.getpath()
                abspath = pkgroot.join(relpath)
                assert pkgroot.join(relpath).check(), (
                        'problem with linkrole :source:`%s`: '
                        'path %s does not exist' % (text, relpath))
            if relpath.endswith('/') or not relpath:
                relpath += 'index.html'
            else:
                relpath += '.html'
            return (text, apigen_relpath + 'source/%s' % (relpath,))
        elif name == 'ref':
            return ("", "") 

    def _checkskip(self, lpath, htmlpath=None):
        if not self.config.getvalue("forcegen"):
            lpath = py.path.local(lpath)
            if htmlpath is not None:
                htmlpath = py.path.local(htmlpath)
            if lpath.ext == '.txt': 
                htmlpath = htmlpath or lpath.new(ext='.html')
                if htmlpath.check(file=1) and htmlpath.mtime() >= lpath.mtime(): 
                    py.test.skip("html file is up to date, use --forcegen to regenerate")
                    #return [] # no need to rebuild 

class DoctestText(py.test.collect.Item): 
    def runtest(self): 
        content = self._normalize_linesep()
        newcontent = self.config.api.pytest_doctest_prepare_content(content=content)
        if newcontent is not None:
            content = newcontent 
        s = content 
        l = []
        prefix = '.. >>> '
        mod = py.std.types.ModuleType(self.fspath.purebasename) 
        skipchunk = False
        for line in deindent(s).split('\n'):
            stripped = line.strip()
            if skipchunk and line.startswith(skipchunk):
                print "skipping", line
                continue
            skipchunk = False 
            if stripped.startswith(prefix):
                try:
                    exec py.code.Source(stripped[len(prefix):]).compile() in \
                        mod.__dict__
                except ValueError, e:
                    if e.args and e.args[0] == "skipchunk":
                        skipchunk = " " * (len(line) - len(line.lstrip()))
                    else:
                        raise
            else:
                l.append(line)
        docstring = "\n".join(l)
        mod.__doc__ = docstring 
        failed, tot = py.compat.doctest.testmod(mod, verbose=1)
        if failed: 
            py.test.fail("doctest %s: %s failed out of %s" %(
                         self.fspath, failed, tot))

    def _normalize_linesep(self):
        # XXX quite nasty... but it works (fixes win32 issues)
        s = self.fspath.read()
        linesep = '\n'
        if '\r' in s:
            if '\n' not in s:
                linesep = '\r'
            else:
                linesep = '\r\n'
        s = s.replace(linesep, '\n')
        return s
        
class LinkCheckerMaker(py.test.collect.Collector): 
    def collect(self):
        return list(self.genlinkchecks())

    def genlinkchecks(self):
        path = self.fspath
        # generating functions + args as single tests 
        timeout = self.config.getvalue("urlcheck_timeout")
        for lineno, line in py.builtin.enumerate(path.readlines()): 
            line = line.strip()
            if line.startswith('.. _'): 
                if line.startswith('.. _`'):
                    delim = '`:'
                else:
                    delim = ':'
                l = line.split(delim, 1)
                if len(l) != 2: 
                    continue
                tryfn = l[1].strip() 
                name = "%s:%d" %(tryfn, lineno)
                if tryfn.startswith('http:') or tryfn.startswith('https'): 
                    if self.config.getvalue("urlcheck"):
                        yield CheckLink(name, parent=self, 
                            args=(tryfn, path, lineno, timeout), callobj=urlcheck)
                elif tryfn.startswith('webcal:'):
                    continue
                else: 
                    i = tryfn.find('#') 
                    if i != -1: 
                        checkfn = tryfn[:i]
                    else: 
                        checkfn = tryfn 
                    if checkfn.strip() and (1 or checkfn.endswith('.html')): 
                        yield CheckLink(name, parent=self, 
                            args=(tryfn, path, lineno), callobj=localrefcheck)
        
class CheckLink(py.test.collect.Function): 
    def repr_metainfo(self):
        return self.ReprMetaInfo(fspath=self.fspath, lineno=self._args[2],
            modpath="checklink: %s" % (self._args[0],))
    def setup(self): 
        pass 
    def teardown(self): 
        pass 

def urlcheck(tryfn, path, lineno, TIMEOUT_URLOPEN): 
    old = py.std.socket.getdefaulttimeout()
    py.std.socket.setdefaulttimeout(TIMEOUT_URLOPEN)
    try:
        try: 
            print "trying remote", tryfn
            py.std.urllib2.urlopen(tryfn)
        finally:
            py.std.socket.setdefaulttimeout(old)
    except (py.std.urllib2.URLError, py.std.urllib2.HTTPError), e: 
        if getattr(e, 'code', None) in (401, 403): # authorization required, forbidden
            py.test.skip("%s: %s" %(tryfn, str(e)))
        else:
            py.test.fail("remote reference error %r in %s:%d\n%s" %(
                         tryfn, path.basename, lineno+1, e))

def localrefcheck(tryfn, path, lineno): 
    # assume it should be a file 
    i = tryfn.find('#')
    if tryfn.startswith('javascript:'):
        return # don't check JS refs
    if i != -1: 
        anchor = tryfn[i+1:]
        tryfn = tryfn[:i]
    else: 
        anchor = ''
    fn = path.dirpath(tryfn) 
    ishtml = fn.ext == '.html' 
    fn = ishtml and fn.new(ext='.txt') or fn
    print "filename is", fn 
    if not fn.check(): # not ishtml or not fn.check(): 
        if not py.path.local(tryfn).check(): # the html could be there 
            py.test.fail("reference error %r in %s:%d" %(
                          tryfn, path.basename, lineno+1))
    if anchor: 
        source = unicode(fn.read(), 'latin1')
        source = source.lower().replace('-', ' ') # aehem

        anchor = anchor.replace('-', ' ') 
        match2 = ".. _`%s`:" % anchor 
        match3 = ".. _%s:" % anchor 
        candidates = (anchor, match2, match3)
        print "candidates", repr(candidates)
        for line in source.split('\n'): 
            line = line.strip()
            if line in candidates: 
                break 
        else: 
            py.test.fail("anchor reference error %s#%s in %s:%d" %(
                tryfn, anchor, path.basename, lineno+1))


#
# PLUGIN tests
#
def test_generic(plugintester):
    plugintester.apicheck(RestdocPlugin)

def test_deindent():
    assert deindent('foo') == 'foo'
    assert deindent('foo\n  bar') == 'foo\n  bar'
    assert deindent('  foo\n  bar\n') == 'foo\nbar\n'
    assert deindent('  foo\n\n  bar\n') == 'foo\n\nbar\n'
    assert deindent(' foo\n  bar\n') == 'foo\n bar\n'
    assert deindent('  foo\n bar\n') == ' foo\nbar\n'

class TestApigenLinkRole:
    disabled = True
    # these tests are moved here from the former py/doc/conftest.py
    def test_resolve_linkrole(self):
        from py.__.doc.conftest import get_apigen_relpath
        apigen_relpath = get_apigen_relpath()

        assert resolve_linkrole('api', 'py.foo.bar', False) == (
            'py.foo.bar', apigen_relpath + 'api/foo.bar.html')
        assert resolve_linkrole('api', 'py.foo.bar()', False) == (
            'py.foo.bar()', apigen_relpath + 'api/foo.bar.html')
        assert resolve_linkrole('api', 'py', False) == (
            'py', apigen_relpath + 'api/index.html')
        py.test.raises(AssertionError, 'resolve_linkrole("api", "foo.bar")')
        assert resolve_linkrole('source', 'py/foo/bar.py', False) == (
            'py/foo/bar.py', apigen_relpath + 'source/foo/bar.py.html')
        assert resolve_linkrole('source', 'py/foo/', False) == (
            'py/foo/', apigen_relpath + 'source/foo/index.html')
        assert resolve_linkrole('source', 'py/', False) == (
            'py/', apigen_relpath + 'source/index.html')
        py.test.raises(AssertionError, 'resolve_linkrole("source", "/foo/bar/")')

    def test_resolve_linkrole_check_api(self):
        assert resolve_linkrole('api', 'py.test.ensuretemp')
        py.test.raises(AssertionError, "resolve_linkrole('api', 'py.foo.baz')")

    def test_resolve_linkrole_check_source(self):
        assert resolve_linkrole('source', 'py/path/common.py')
        py.test.raises(AssertionError,
                       "resolve_linkrole('source', 'py/foo/bar.py')")


def pytest_funcarg__testdir(__call__, pyfuncitem):
    testdir = __call__.execute(firstresult=True)
    testdir.makepyfile(confrest="from py.__.misc.rest import Project")
    testdir.plugins.append(RestdocPlugin())
    return testdir
    
class TestDoctest:
    def test_doctest_extra_exec(self, testdir):
        xtxt = testdir.maketxtfile(x="""
            hello::
                .. >>> raise ValueError 
                   >>> None
        """)
        sorter = testdir.inline_run(xtxt)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 1

    def test_doctest_basic(self, testdir): 
        xtxt = testdir.maketxtfile(x="""
            .. 
               >>> from os.path import abspath 

            hello world 

               >>> assert abspath 
               >>> i=3
               >>> print i
               3

            yes yes

                >>> i
                3

            end
        """)
        sorter = testdir.inline_run(xtxt)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0 
        assert passed + skipped == 2

    def test_doctest_eol(self, testdir): 
        ytxt = testdir.maketxtfile(y=".. >>> 1 + 1\r\n   2\r\n\r\n")
        sorter = testdir.inline_run(ytxt)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0 
        assert passed + skipped == 2

    def test_doctest_indentation(self, testdir):
        footxt = testdir.maketxtfile(foo=
            '..\n  >>> print "foo\\n  bar"\n  foo\n    bar\n')
        sorter = testdir.inline_run(footxt)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0
        assert skipped + passed == 2 

    def test_js_ignore(self, testdir):
        xtxt = testdir.maketxtfile(xtxt="""
            `blah`_

            .. _`blah`: javascript:some_function()
        """)
        sorter = testdir.inline_run(xtxt)
        passed, skipped, failed = sorter.countoutcomes()
        assert failed == 0
        assert skipped + passed == 3 

    def test_pytest_doctest_prepare_content(self, testdir):
        l = []
        class MyPlugin:
            def pytest_doctest_prepare_content(self, content):
                l.append(content)
                return content.replace("False", "True")

        testdir.plugins.append(MyPlugin())

        xtxt = testdir.maketxtfile(x="""
            hello:

                >>> 2 == 2
                False

        """)
        sorter = testdir.inline_run(xtxt)
        assert len(l) == 1
        passed, skipped, failed = sorter.countoutcomes()
        assert passed >= 1
        assert not failed 
        assert skipped <= 1
