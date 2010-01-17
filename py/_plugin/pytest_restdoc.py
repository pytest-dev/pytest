"""
perform ReST syntax, local and remote reference tests on .rst/.txt files. 
"""
import py
import sys, os, re

def pytest_addoption(parser):
    group = parser.getgroup("ReST", "ReST documentation check options")
    group.addoption('-R', '--urlcheck',
           action="store_true", dest="urlcheck", default=False, 
           help="urlopen() remote links found in ReST text files.") 
    group.addoption('--urltimeout', action="store", metavar="secs",
        type="int", dest="urlcheck_timeout", default=5,
        help="timeout in seconds for remote urlchecks")
    group.addoption('--forcegen',
           action="store_true", dest="forcegen", default=False,
           help="force generation of html files.")

def pytest_collect_file(path, parent):
    if path.ext in (".txt", ".rst"):
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
    def __init__(self, fspath, parent, project):
        super(ReSTFile, self).__init__(fspath=fspath, parent=parent)
        self.project = project

    def collect(self):
        return [
            ReSTSyntaxTest("ReSTSyntax", parent=self, project=self.project),
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
    for i, line in enumerate(lines):
        if not line.strip():
            lines[i] = ''
        else:
            lines[i] = line[leastspaces:]
    return sep.join(lines)

class ReSTSyntaxTest(py.test.collect.Item): 
    def __init__(self, name, parent, project):
        super(ReSTSyntaxTest, self).__init__(name=name, parent=parent)
        self.project = project

    def reportinfo(self):
        return self.fspath, None, "syntax check"

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
        #directive.register_linkrole('api', self.resolve_linkrole)
        #directive.register_linkrole('source', self.resolve_linkrole)
#
#        # XXX fake sphinx' "toctree" and refs
#        directive.register_linkrole('ref', self.resolve_linkrole)
        
        from docutils.parsers.rst import directives
        def toctree_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
            return []
        toctree_directive.content = 1
        toctree_directive.options = {'maxdepth': int, 'glob': directives.flag,
                             'hidden': directives.flag}
        directives.register_directive('toctree', toctree_directive)
        self.register_pygments()

    def register_pygments(self):
        # taken from pygments-main/external/rst-directive.py 
        from docutils.parsers.rst import directives
        try:
            from pygments.formatters import HtmlFormatter
        except ImportError:
            def pygments_directive(name, arguments, options, content, lineno,
                                   content_offset, block_text, state, state_machine):
                return []
            pygments_directive.options = {}
        else:
            # The default formatter
            DEFAULT = HtmlFormatter(noclasses=True)
            # Add name -> formatter pairs for every variant you want to use
            VARIANTS = {
                # 'linenos': HtmlFormatter(noclasses=INLINESTYLES, linenos=True),
            }

            from docutils import nodes

            from pygments import highlight
            from pygments.lexers import get_lexer_by_name, TextLexer

            def pygments_directive(name, arguments, options, content, lineno,
                                   content_offset, block_text, state, state_machine):
                try:
                    lexer = get_lexer_by_name(arguments[0])
                except ValueError:
                    # no lexer found - use the text one instead of an exception
                    lexer = TextLexer()
                # take an arbitrary option if more than one is given
                formatter = options and VARIANTS[options.keys()[0]] or DEFAULT
                parsed = highlight('\n'.join(content), lexer, formatter)
                return [nodes.raw('', parsed, format='html')]

            pygments_directive.options = dict([(key, directives.flag) for key in VARIANTS])

        pygments_directive.arguments = (1, 0, 1)
        pygments_directive.content = 1
        directives.register_directive('sourcecode', pygments_directive)

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
                pkgroot = py._pydir
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
    def reportinfo(self):
        return self.fspath, None, "doctest"

    def runtest(self): 
        content = self._normalize_linesep()
        newcontent = self.config.hook.pytest_doctest_prepare_content(content=content)
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
                py.builtin.print_("skipping", line)
                continue
            skipchunk = False 
            if stripped.startswith(prefix):
                try:
                    py.builtin.exec_(py.code.Source(
                            stripped[len(prefix):]).compile(),  mod.__dict__)
                except ValueError:
                    e = sys.exc_info()[1]
                    if e.args and e.args[0] == "skipchunk":
                        skipchunk = " " * (len(line) - len(line.lstrip()))
                    else:
                        raise
            else:
                l.append(line)
        docstring = "\n".join(l)
        mod.__doc__ = docstring 
        failed, tot = py.std.doctest.testmod(mod, verbose=1)
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
        for lineno, line in enumerate(path.readlines()): 
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
                            args=(tryfn, path, lineno, timeout), checkfunc=urlcheck)
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
                            args=(tryfn, path, lineno), checkfunc=localrefcheck)
        
class CheckLink(py.test.collect.Item):
    def __init__(self, name, parent, args, checkfunc):
        super(CheckLink, self).__init__(name, parent)
        self.args = args
        self.checkfunc = checkfunc

    def runtest(self):
        return self.checkfunc(*self.args)

    def reportinfo(self, basedir=None):
        return (self.fspath, self.args[2], "checklink: %s" % self.args[0])

def urlcheck(tryfn, path, lineno, TIMEOUT_URLOPEN): 
    old = py.std.socket.getdefaulttimeout()
    py.std.socket.setdefaulttimeout(TIMEOUT_URLOPEN)
    try:
        try: 
            py.builtin.print_("trying remote", tryfn)
            py.std.urllib2.urlopen(tryfn)
        finally:
            py.std.socket.setdefaulttimeout(old)
    except (py.std.urllib2.URLError, py.std.urllib2.HTTPError): 
        e = sys.exc_info()[1]
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
    py.builtin.print_("filename is", fn)
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
        py.builtin.print_("candidates", repr(candidates))
        for line in source.split('\n'): 
            line = line.strip()
            if line in candidates: 
                break 
        else: 
            py.test.fail("anchor reference error %s#%s in %s:%d" %(
                tryfn, anchor, path.basename, lineno+1))

if hasattr(sys.stdout, 'fileno') and os.isatty(sys.stdout.fileno()):
    def log(msg):
        print(msg)
else:
    def log(msg):
        pass

def convert_rest_html(source, source_path, stylesheet=None, encoding='latin1'):
    """ return html latin1-encoded document for the given input. 
        source  a ReST-string
        sourcepath where to look for includes (basically)
        stylesheet path (to be used if any)
    """
    from docutils.core import publish_string
    kwargs = {
        'stylesheet' : stylesheet, 
        'stylesheet_path': None,
        'traceback' : 1, 
        'embed_stylesheet': 0,
        'output_encoding' : encoding, 
        #'halt' : 0, # 'info',
        'halt_level' : 2, 
    }
    # docutils uses os.getcwd() :-(
    source_path = os.path.abspath(str(source_path))
    prevdir = os.getcwd()
    try:
        #os.chdir(os.path.dirname(source_path))
        return publish_string(source, source_path, writer_name='html',
                              settings_overrides=kwargs)
    finally:
        os.chdir(prevdir)

def process(txtpath, encoding='latin1'):
    """ process a textfile """
    log("processing %s" % txtpath)
    assert txtpath.check(ext='.txt')
    if isinstance(txtpath, py.path.svnwc):
        txtpath = txtpath.localpath
    htmlpath = txtpath.new(ext='.html')
    #svninfopath = txtpath.localpath.new(ext='.svninfo')

    style = txtpath.dirpath('style.css')
    if style.check():
        stylesheet = style.basename
    else:
        stylesheet = None
    content = unicode(txtpath.read(), encoding)
    doc = convert_rest_html(content, txtpath, stylesheet=stylesheet, encoding=encoding)
    htmlpath.open('wb').write(doc)
    #log("wrote %r" % htmlpath)
    #if txtpath.check(svnwc=1, versioned=1): 
    #    info = txtpath.info()
    #    svninfopath.dump(info) 

if sys.version_info > (3, 0):
    def _uni(s): return s
else:
    def _uni(s):
        return unicode(s)

rex1 = re.compile(r'.*<body>(.*)</body>.*', re.MULTILINE | re.DOTALL)
rex2 = re.compile(r'.*<div class="document">(.*)</div>.*', re.MULTILINE | re.DOTALL)

def strip_html_header(string, encoding='utf8'):
    """ return the content of the body-tag """ 
    uni = unicode(string, encoding)
    for rex in rex1,rex2: 
        match = rex.search(uni) 
        if not match: 
            break 
        uni = match.group(1) 
    return uni 

class Project: # used for confrest.py files 
    def __init__(self, sourcepath):
        self.sourcepath = sourcepath
    def process(self, path):
        return process(path)
    def get_htmloutputpath(self, path):
        return path.new(ext='html')
