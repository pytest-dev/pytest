from __future__ import generators
import py
from py.__.misc import rest 
from py.__.apigen.linker import relpath
import os

pypkgdir = py.path.local(py.__file__).dirpath()

mypath = py.magic.autopath().dirpath()

TIMEOUT_URLOPEN = 5.0

Option = py.test.config.Option 
option = py.test.config.addoptions("documentation check options", 
        Option('-R', '--checkremote',
               action="store_true", dest="checkremote", default=False, 
               help="urlopen() remote links found in ReST text files.", 
        ), 
        Option('', '--forcegen',
               action="store_true", dest="forcegen", default=False,
               help="force generation of html files even if they appear up-to-date"
        ),
) 

def get_apigenpath():
    from py.__.conftest import option
    path = os.environ.get('APIGENPATH')
    if path is None:
        path = option.apigenpath
    return pypkgdir.join(path, abs=True)

def get_docpath():
    from py.__.conftest import option
    path = os.environ.get('DOCPATH')
    if path is None:
        path = option.docpath
    return pypkgdir.join(path, abs=True)

def get_apigen_relpath():
    return relpath(get_docpath().strpath + '/',
                   get_apigenpath().strpath + '/')

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

_initialized = False
def checkdocutils():
    global _initialized
    py.test.importorskip("docutils")
    if not _initialized:
        from py.__.rest import directive
        directive.register_linkrole('api', resolve_linkrole)
        directive.register_linkrole('source', resolve_linkrole)
        _initialized = True

def restcheck(path):
    localpath = path
    if hasattr(path, 'localpath'):
        localpath = path.localpath
    checkdocutils() 
    import docutils.utils

    try: 
        cur = localpath
        for x in cur.parts(reverse=True):
            confrest = x.dirpath('confrest.py')
            if confrest.check(file=1): 
                confrest = confrest.pyimport()
                project = confrest.Project()
                _checkskip(path, project.get_htmloutputpath(path))
                project.process(path) 
                break
        else: 
            # defer to default processor 
            _checkskip(path)
            rest.process(path) 
    except KeyboardInterrupt: 
        raise 
    except docutils.utils.SystemMessage: 
        # we assume docutils printed info on stdout 
        py.test.fail("docutils processing failed, see captured stderr") 

def _checkskip(lpath, htmlpath=None):
    if not option.forcegen:
        lpath = py.path.local(lpath)
        if htmlpath is not None:
            htmlpath = py.path.local(htmlpath)
        if lpath.ext == '.txt': 
            htmlpath = htmlpath or lpath.new(ext='.html')
            if htmlpath.check(file=1) and htmlpath.mtime() >= lpath.mtime(): 
                py.test.skip("html file is up to date, use --forcegen to regenerate")
                #return [] # no need to rebuild 

class ReSTSyntaxTest(py.test.collect.Item): 
    def runtest(self):
        mypath = self.fspath 
        restcheck(py.path.svnwc(mypath))

class DoctestText(py.test.collect.Item): 
    def runtest(self): 
        s = self._normalize_linesep()
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
        l = [] 
        for call, tryfn, path, lineno in genlinkchecks(self.fspath): 
            name = "%s:%d" %(tryfn, lineno)
            l.append(
                CheckLink(name, parent=self, args=(tryfn, path, lineno), callobj=call)
            )
        return l
        
class CheckLink(py.test.collect.Function): 
    def repr_metainfo(self):
        return self.ReprMetaInfo(fspath=self.fspath, lineno=self._args[2],
            modpath="checklink: %s" % (self._args[0],))
    def setup(self): 
        pass 
    def teardown(self): 
        pass 

class DocfileTests(py.test.collect.File):
    DoctestText = DoctestText
    ReSTSyntaxTest = ReSTSyntaxTest
    LinkCheckerMaker = LinkCheckerMaker
    
    def collect(self):
        return [
            self.ReSTSyntaxTest(self.fspath.basename, parent=self),
            self.LinkCheckerMaker("checklinks", self),
            self.DoctestText("doctest", self),
        ]

# generating functions + args as single tests 
def genlinkchecks(path): 
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
            if tryfn.startswith('http:') or tryfn.startswith('https'): 
                if option.checkremote: 
                    yield urlcheck, tryfn, path, lineno 
            elif tryfn.startswith('webcal:'):
                continue
            else: 
                i = tryfn.find('#') 
                if i != -1: 
                    checkfn = tryfn[:i]
                else: 
                    checkfn = tryfn 
                if checkfn.strip() and (1 or checkfn.endswith('.html')): 
                    yield localrefcheck, tryfn, path, lineno 

def urlcheck(tryfn, path, lineno): 
    old = py.std.socket.getdefaulttimeout()
    py.std.socket.setdefaulttimeout(TIMEOUT_URLOPEN)
    try:
        try: 
            print "trying remote", tryfn
            py.std.urllib2.urlopen(tryfn)
        finally:
            py.std.socket.setdefaulttimeout(old)
    except (py.std.urllib2.URLError, py.std.urllib2.HTTPError), e: 
        if e.code in (401, 403): # authorization required, forbidden
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


# ___________________________________________________________
# 
# hooking into py.test Directory collector's chain ... 

class DocDirectory(py.test.collect.Directory): 
    DocfileTests = DocfileTests
    def collect(self):
        results = super(DocDirectory, self).collect() 
        for x in self.fspath.listdir('*.txt', sort=True): 
            results.append(self.DocfileTests(x, parent=self))
        return results 

Directory = DocDirectory

def resolve_linkrole(name, text, check=True):
    apigen_relpath = get_apigen_relpath()
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

# legacy
ReSTChecker = DocfileTests
